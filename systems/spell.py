from pygame import Surface, Vector2
import pygame
from engine.ecs import Entity, EntityGroup, enumerate_component, factory
from systems.controls import ControlComponent
from systems.effect import EffectComponent, create_effect
from systems.motion import Direction, MotionComponent
from systems.sprites import CameraComponent
from systems.tilemap import TilemapComponent, Tile
from systems.turn import TurnComponent
from systems.ui import UIComponent

from . import tilemap
from . import utils

@enumerate_component("spell")
class SpellComponent:
    select_action: str
    effect: str = "wave"
    initial_tile: list[Tile] = factory(list)
    color: tuple[int,int,int]


@enumerate_component("selected_spell")
class SelectedSpellComponent:
    spell_action: str = None
    spell_casting_start: Vector2 = None
    target_tile: list[Tile] = None
    spell_color: tuple[int,int,int] = None

@enumerate_component("tile_area")
class TileAreaComponent:
    tile_positions: list[Vector2] = factory(list)


def find_positions(map: TilemapComponent, coords: Vector2, value, checked = []):
    tile = map.get_tile(coords)
    positions = []

    if tile == value and coords not in checked:
        positions.append(coords)

        for check_coord in utils.vector_cardinals(coords):
            if check_coord in checked:
                continue

            positions += find_positions(map, check_coord, value, checked + positions)

    return positions

def spell_tile_detection_system(group: EntityGroup):
    motion: MotionComponent = group.query_singleton('player', 'motion').motion
    tilemap: TilemapComponent = group.query_singleton('tilemap').tilemap
    selected_spell_entity = group.query_singleton('selected_spell', 'tile_area')
    selected_spell: SelectedSpellComponent = selected_spell_entity.selected_spell
    tile_area: TileAreaComponent = selected_spell_entity.tile_area
    positions = []

    for v in utils.vector_cardinals(motion.position):
        tile = tilemap.get_tile(v)
        if tile in selected_spell.target_tile:
            positions += find_positions(tilemap, v, tile, positions)

    tile_area.tile_positions = positions
    

def spell_select_system(group: EntityGroup):
    actions = group.query_singleton('controls').controls.actions
    selected_spell_entity = group.query_singleton('selected_spell', 'ui')
    selected_spell: SelectedSpellComponent = selected_spell_entity.selected_spell
    ui: UIComponent = selected_spell_entity.ui

    for spell_entity in group.query('spell'):
        spell: SpellComponent = spell_entity.spell

        if spell.select_action in actions or selected_spell.spell_action is None:
            selected_spell.spell_action = spell.select_action
            selected_spell.target_tile = spell.initial_tile
            selected_spell.spell_color = spell.color
            ui.text = spell_entity.name
            break


def spell_cast_system(group: EntityGroup):
    controls: ControlComponent = group.query_singleton('controls').controls
    game = group.query_singleton('game').game
    selected_spell_entity: SelectedSpellComponent = group.query_singleton('selected_spell', 'tile_area')
    selected_spell_entity: SelectedSpellComponent = selected_spell_entity
    selected_spell: SelectedSpellComponent = selected_spell_entity.selected_spell
    tile_area: TileAreaComponent = selected_spell_entity.tile_area
    turn: TurnComponent = group.query_singleton('turn').turn

    if not turn.waiting or game.state != game.STATE_PLAYING:
        return
    
    if selected_spell.spell_casting_start:
        camera_entity = group.query_singleton('camera', 'motion')
        camera: CameraComponent = camera_entity.camera
        offset, scale = camera.get_screenspace_transform(camera_entity.motion.position)
        effect_direction = utils.closest_cardinal(controls.mouse_grid_position - selected_spell.spell_casting_start)
        if selected_spell.spell_color:
            surface = Surface(Vector2(scale*2), pygame.SRCALPHA)
            pygame.draw.line(surface, selected_spell.spell_color, Vector2(scale), Vector2(scale) + (effect_direction * scale), 5)
            pygame.draw.circle(surface, selected_spell.spell_color, Vector2(scale), 8)
            camera.surface.blit(surface, (selected_spell.spell_casting_start * scale + offset) - Vector2(scale))

            sq = pygame.surface.Surface(Vector2(scale), pygame.SRCALPHA)
            pygame.draw.polygon(sq, selected_spell.spell_color, [(1,1), (1,scale-1), (scale-1,scale-1), (scale-1,1)], 1)
            for coord in tile_area.tile_positions:
                ss_coord = (coord * scale) + offset - Vector2(scale/2)
                camera.surface.blit(sq, ss_coord)
        

    if "mouse_0_start" in controls.actions:
        selected_spell.spell_casting_start = controls.mouse_grid_position
    if "mouse_0_stop" in controls.actions:
        for spell_entity in group.query('spell'):
            spell: SpellComponent = spell_entity.spell
            
            if spell.select_action == selected_spell.spell_action and selected_spell.spell_casting_start in tile_area.tile_positions:
                effect_entity = create_effect(spell.effect, selected_spell.spell_casting_start, effect_direction)
                group.add(effect_entity)
                turn.waiting = False
                break
        selected_spell.spell_casting_start = None


def mount_spell_system(group: EntityGroup):

    water_wave = Entity("Water wave")
    water_wave.spell = SpellComponent(select_action="select_spell_1", effect="wave", initial_tile=[tilemap.TILE_WATER], color=(0,0,255))
    plant_growth = Entity("Brambles")
    plant_growth.spell = SpellComponent(select_action="select_spell_2", effect="growth", initial_tile=[tilemap.TILE_MUD, tilemap.TILE_ASH], color=(0,255,0))
    spark = Entity("Ignite")
    spark.spell = SpellComponent(select_action="select_spell_3", effect="fire", initial_tile=[tilemap.TILE_PLANT], color=(255,0,0))
    fire_lance = Entity("Spark lance")
    fire_lance.spell = SpellComponent(select_action="select_spell_4", effect="spark", initial_tile=[tilemap.TILE_EMBER, tilemap.TILE_MARSH], color=(255,255,0))
    corrupt_fill = Entity("Corrupt")
    corrupt_fill.spell = SpellComponent(select_action="select_spell_5", effect="corrupt", initial_tile=[tilemap.TILE_BONES], color=(127,0,127))
    purify_fill = Entity("Purify")
    purify_fill.spell = SpellComponent(select_action="select_spell_6", effect="purify", initial_tile=[tilemap.TILE_BONES], color=(255,255,200))

    selected_spell_entity = Entity("selected_spell")
    selected_spell_entity.selected_spell = SelectedSpellComponent()
    selected_spell_entity.ui = UIComponent(text="")
    selected_spell_entity.motion = MotionComponent(position=Vector2(10, 50))
    selected_spell_entity.tile_area = TileAreaComponent()

    group.add_all(water_wave, plant_growth, spark, fire_lance, corrupt_fill, purify_fill)
    group.add(selected_spell_entity)

    group.mount_system(spell_select_system)
    group.mount_system(spell_tile_detection_system)
    group.mount_system(spell_cast_system)