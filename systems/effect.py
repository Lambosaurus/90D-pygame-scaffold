from engine.ecs import Entity, EntityGroup, enumerate_component, factory
from pygame import Vector2
from dataclasses import dataclass
import random
import math

from systems.sounds import SoundComponent

from .sprites import SpriteComponent
from .motion import MotionComponent
from .tilemap import TilemapComponent
from .collision import CollisionComponent
from .health import HealthComponent
from . import turn
from . import tilemap
from . import utils
from . import motion


SHAPE_NONE = 0
SHAPE_WAVE = 1
SHAPE_FILL = 2
SHAPE_LANCE = 3


'''
Component class to store effect information
'''
@enumerate_component("effect")
class EffectComponent():
    name: str
    direction: Vector2 = factory(Vector2)
    energy: int = 1
    shape: int = SHAPE_NONE
    harvests: dict[int,tuple[int,int]] = factory(dict)
    chains_to: dict[int,tuple[float,int]] = factory(dict)
    cast_from: list[int]
    propagates_to: list[int] = factory(list)
    damage: int = 0
    consumes: list[str] = factory(list)

    def add_harvest(self, tile_in: int, tile_out: int, energy: int, propagates: bool = False):
        self.harvests[tile_in] = (tile_out, energy)
        if propagates:
            self.propagates_to.append(tile_in)

    def add_chain(self, tile_in: int, probability: float = 1.0, energy: int = 0):
        self.chains_to[tile_in] = (probability, energy)

    def add_consumes(self, name: str):
        self.consumes.append(name)

    def requires_direction(self):
        return self.shape != SHAPE_NONE


'''
Enumerates through the valid targets for a given effect
'''
def valid_tiles(map: TilemapComponent, valid: list[int], coords: list[Vector2]):
    return [ coord for coord in coords if (map.get_tile(coord) in valid) ]

'''
Shuffles the list.
Note this mutates the given list. I dont care.
'''
def shuffled(items: list) -> list:
    items = list(items)
    random.shuffle(items)
    return items


def try_harvest(map: TilemapComponent, pos: Vector2, effect: EffectComponent):
    tile = map.get_tile(pos)
    if tile in effect.harvests:
        new_tile, energy_gain = effect.harvests[tile]
        map.set_tile(pos, new_tile)
        effect.energy += energy_gain


def apply_damage(collision: CollisionComponent, pos: Vector2, damage: int):
    for e in collision.get_entities_at(pos, motion.LAYER_PLAYER):
        health: HealthComponent = e.health
        health.health -= damage

    for e in collision.get_entities_at(pos, motion.LAYER_ENEMIES):
        health: HealthComponent = e.health
        health.health -= damage

'''
The effect update system:
Handles effect propigation and decay (probably)
'''
def effect_update_system(group: EntityGroup):

    t: turn.TurnComponent = group.query_singleton("turn").turn

    if t.state != turn.TURN_EFFECTS:
        return
    
    map: TilemapComponent = group.query_singleton('tilemap').tilemap
    collision: CollisionComponent = group.query_singleton('collision').collision

    for e in group.query("effect", "motion"):
        
        effect: EffectComponent = e.effect
        motion: MotionComponent = e.motion
        pos = motion.position
        dir = effect.direction

        # Harvesting
        try_harvest(map, pos, effect)
        
        # Propagation
        if effect.energy > 1:

            apply_damage(collision, pos, effect.damage)

            # A list of places we would like to try propagate to.
            # (position, energy, shape)
            propagation_request: list[tuple[Vector2, int, int]] = []
            unchecked_coords = []

            # Do the forced propagation, which is shape specific
            if effect.shape == SHAPE_WAVE:
                # Waves transfer all energy forward.
                propagation_request = [
                    (pos + dir, effect.energy - 1, SHAPE_WAVE),
                ]

                # Waves start waves in valid adjacent tiles
                for coord in valid_tiles(map, effect.propagates_to, utils.vector_normals(pos, dir)):
                    propagation_request.append( (coord, 0, SHAPE_WAVE) )
                unchecked_coords = [pos-dir]

            elif effect.shape == SHAPE_FILL:
                # Goes out in all directions
                valid_coords = valid_tiles(map, effect.propagates_to, shuffled(utils.vector_cardinals(pos)))
                # Let the propagation step figure out if we use more energy than we have...
                if len(valid_coords):
                    energy_transfer =  math.ceil(effect.energy) / len(valid_coords)
                    for coord in valid_coords:
                        propagation_request.append( (coord, energy_transfer, SHAPE_FILL) )

            elif effect.shape == SHAPE_LANCE:
                # Goes forward only
                propagation_request = [
                    (pos + dir, effect.energy - 1, SHAPE_LANCE),
                ]
                unchecked_coords = list(utils.vector_normals(pos, dir)) + [-dir]

            else: # SHAPE_NONE
                unchecked_coords = utils.vector_cardinals(pos)

            # Do the random propagation in the unchecked directions
            for coord in shuffled( valid_tiles(map, effect.chains_to, unchecked_coords) ):
                probability, energy = effect.chains_to[map.get_tile(coord)]
                if random.random() < probability:
                    propagation_request.append( (coord, energy, SHAPE_NONE) )
            
            # Apply the propagation requests
            for coord, energy, shape in propagation_request:
                
                blocked = False
                for other in collision.get_entities_at(coord, e.motion.layer):
                    if other.effect.name in effect.consumes:
                        other.effect.energy = 0
                        group.remove(other)
                    else:
                        blocked = True

                if not blocked:
                    energy = min(energy, max(0, effect.energy -1))
                    new_entity = propagate_entity(e, coord, energy, shape)
                    try_harvest(map, coord, new_entity.effect)
                    apply_damage(collision, coord, effect.damage)
                    group.add(new_entity)

        # decay
        effect.energy -= 1
        if effect.energy <= 0:
            group.remove(e)


'''
Propagates an existing effect, inheriting some energy. Shape may be overridden here.
'''
def propagate_entity(e: Entity, position: Vector2, energy: int, shape: int | None = None) -> Entity:
    # Remove the energy from the previous effect
    e.effect.energy -= energy

    # Create the new effect
    e = e.clone()
    e.motion.position = position
    e.effect.energy = energy
    if e.contains('sound'):
        e.sound.state = SoundComponent.STATE_PLAY

    # The shape may be overridden
    if shape != None:
        e.effect.shape = shape

    return e


'''
Instantiate all the template effects. These can be cloned when required
'''
def create_effect_templates():
    effect_dict = {}

    e = Entity("effect-fire")
    e.motion = MotionComponent(layer=motion.LAYER_EFFECTS)
    e.sprite = SpriteComponent.from_resource("effects/fire.png")
    e.effect = EffectComponent(name="fire", cast_from=[tilemap.TILE_PLANT], shape=SHAPE_WAVE, damage=200)
    e.effect.add_harvest(tilemap.TILE_PLANT, tilemap.TILE_EMBER, 3, True)
    e.effect.add_harvest(tilemap.TILE_WATER, tilemap.TILE_MUD, -3)
    e.effect.add_harvest(tilemap.TILE_MUD, tilemap.TILE_EARTH, -1)
    e.effect.add_harvest(tilemap.TILE_ICE, tilemap.TILE_WATER, -3)
    e.effect.add_harvest(tilemap.TILE_ROCK, tilemap.TILE_LAVA, -5)
    e.effect.add_chain(tilemap.TILE_PLANT, 0.5)
    e.effect.add_consumes("growth")
    e.sound = SoundComponent(sound_file='assets/sounds/fire.mp3', volume=0.5, state=0)
    effect_dict[e.effect.name] = e

    e = Entity("effect-wave")
    e.motion = MotionComponent(layer=motion.LAYER_EFFECTS)
    e.sprite = SpriteComponent.from_resource("effects/water.png")
    e.effect = EffectComponent(name="wave", cast_from=[tilemap.TILE_WATER],shape=SHAPE_WAVE, damage=100)
    e.effect.add_harvest(tilemap.TILE_WATER, tilemap.TILE_MUD, 3, True)
    e.effect.add_harvest(tilemap.TILE_EARTH, tilemap.TILE_MUD, 0)
    e.effect.add_harvest(tilemap.TILE_EMBER, tilemap.TILE_ROCK, -1)
    e.sound = SoundComponent(sound_file='assets/sounds/splash.mp3', volume=0.5, state=0)
    effect_dict[e.effect.name] = e

    e = Entity("effect-growth")
    e.motion = MotionComponent(layer=motion.LAYER_EFFECTS)
    e.sprite = SpriteComponent.from_resource("effects/growth.png")
    e.effect = EffectComponent(name="growth",cast_from=[tilemap.TILE_MUD, tilemap.TILE_ASH], damage=25)
    e.effect.add_harvest(tilemap.TILE_MUD, tilemap.TILE_PLANT, 10, True)
    e.effect.add_harvest(tilemap.TILE_EARTH, tilemap.TILE_PLANT, 0)
    e.effect.add_harvest(tilemap.TILE_ASH, tilemap.TILE_MARSH, 7, True)
    e.effect.add_chain(tilemap.TILE_MUD, 0.25)
    e.effect.add_chain(tilemap.TILE_EARTH, 0.25)
    e.effect.add_chain(tilemap.TILE_ASH, 0.25)
    e.sound = SoundComponent(sound_file='assets/sounds/grow.mp3', volume=0.5, state=0)
    effect_dict[e.effect.name] = e

    e = Entity("effect-spark")
    e.motion = MotionComponent(layer=motion.LAYER_EFFECTS)
    e.sprite = SpriteComponent.from_resource("effects/spark.png")
    e.effect = EffectComponent(name="spark",cast_from=[tilemap.TILE_EMBER,tilemap.TILE_MARSH], shape=SHAPE_LANCE, damage=300)
    e.effect.add_harvest(tilemap.TILE_EMBER, tilemap.TILE_EARTH, 2, True)
    e.effect.add_harvest(tilemap.TILE_MARSH, tilemap.TILE_OOZE, 2, True)
    e.effect.add_chain(tilemap.TILE_EMBER, 0.15)
    e.effect.add_chain(tilemap.TILE_MARSH, 0.15)
    e.sound = SoundComponent(sound_file='assets/sounds/zap.mp3', volume=0.5, state=0)
    effect_dict[e.effect.name] = e

    e = Entity("effect-ice")
    e.motion = MotionComponent(layer=motion.LAYER_EFFECTS)
    e.sprite = SpriteComponent.from_resource("effects/ice.png")
    e.effect = EffectComponent(name="ice", cast_from=[tilemap.TILE_WATER], shape=SHAPE_LANCE, damage=100)
    e.effect.add_harvest(tilemap.TILE_WATER, tilemap.TILE_ICE, 2, True)
    e.effect.add_harvest(tilemap.TILE_HELLSCAPE, tilemap.TILE_ASH, 1, True)
    e.sound = SoundComponent(sound_file='assets/sounds/ice.mp3', volume=0.5, state=0)
    effect_dict[e.effect.name] = e

    e = Entity("effect-corrupt")
    e.motion = MotionComponent(layer=motion.LAYER_EFFECTS)
    e.sprite = SpriteComponent.from_resource("effects/corrupt.png")
    e.effect = EffectComponent(name="corrupt", cast_from=[tilemap.TILE_BONES], shape=SHAPE_FILL, damage=25)
    e.effect.add_harvest(tilemap.TILE_ICE, tilemap.TILE_OOZE, 2, True)
    e.effect.add_harvest(tilemap.TILE_MUD, tilemap.TILE_MARSH, 2, True)
    e.effect.add_harvest(tilemap.TILE_EMBER, tilemap.TILE_ASH, 2, True)
    e.effect.add_harvest(tilemap.TILE_LAVA, tilemap.TILE_HELLSCAPE, 2, True)
    e.effect.add_harvest(tilemap.TILE_BONES, tilemap.TILE_EARTH, 4, True)
    e.sound = SoundComponent(sound_file='assets/sounds/curse.mp3', volume=0.5, state=0)
    effect_dict[e.effect.name] = e

    e = Entity("effect-purify")
    e.motion = MotionComponent(layer=motion.LAYER_EFFECTS)
    e.sprite = SpriteComponent.from_resource("effects/purify.png")
    e.effect = EffectComponent(name="purify", cast_from=[tilemap.TILE_BONES], shape=SHAPE_FILL, damage=0)
    e.effect.add_harvest(tilemap.TILE_OOZE, tilemap.TILE_WATER, 2, True)
    e.effect.add_harvest(tilemap.TILE_MARSH, tilemap.TILE_MUD, 2, True)
    e.effect.add_harvest(tilemap.TILE_ASH, tilemap.TILE_EMBER, 2, True)
    e.effect.add_harvest(tilemap.TILE_HELLSCAPE, tilemap.TILE_LAVA, 2, True)
    e.effect.add_harvest(tilemap.TILE_BONES, tilemap.TILE_EARTH, 4, True)
    e.sound = SoundComponent(sound_file='assets/sounds/purify.mp3', volume=0.5, state=0)
    effect_dict[e.effect.name] = e
    
    return effect_dict

EFFECT_TEMPLATES = create_effect_templates()


'''
Spawns a new effect (as per a spell)
'''
def create_effect(type: str, position: Vector2, direction: Vector2 = Vector2(0)) -> Entity:
    e = EFFECT_TEMPLATES[type].clone()
    e.motion.position = Vector2(position)
    e.effect.direction = direction
    return e


'''
Mounts the effect updating system
'''
def mount_effect_system(group: EntityGroup):
    group.mount_system(effect_update_system)
