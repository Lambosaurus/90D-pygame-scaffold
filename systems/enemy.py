from pygame import Vector2
from engine.ecs import Entity, EntityGroup, enumerate_component
from systems.sounds import SoundComponent
from .motion import MotionComponent
from .sprites import SpriteComponent
from .player import PlayerComponent
from .turn import TurnComponent
from .health import HealthComponent
from .tilemap import TilemapComponent
from . import turn
from . import motion
from . import tilemap

from math import copysign
from random import choice
from queue import PriorityQueue

'''
A component that represents a generic enemy
'''
@enumerate_component("enemy")
class EnemyComponent:
    damage: int

'''
Update enemy systems including motion and when to do damage to player
(based on sharing same position on grid)
'''
def enemy_update_system(group: EntityGroup):

    player = group.query_singleton('player')
    t: TurnComponent = group.query_singleton('turn').turn
    tm: TilemapComponent = group.query_singleton('tilemap').tilemap

    for e in group.query('enemy', 'health'):

        if t.state == turn.TURN_ENEMY:
            motion: MotionComponent = e.motion
            mtp = a_star(tm.map, (e.motion.position.x, e.motion.position.y), (player.motion.position.x, player.motion.position.y))
            motion.velocity = mtp

            if player.motion.position == e.motion.position:
                hurt_sound = Entity('sound')
                hurt_sound.sound = SoundComponent(sound_file='assets/sounds/enemy-death.mp3', volume=0.25, state=0, destroy_after_play=True)
                hurt_sound.motion = MotionComponent(position=e.motion.position)

                group.add(hurt_sound)

                player.health.health -= e.enemy.damage
                group.remove(e)
                
        if not e.health.is_alive:
            tm.set_tile(e.motion.position, tilemap.TILE_BONES)
            group.remove(e)


'''
Mount system
'''
def mount_enemy_system(group: EntityGroup):
    group.mount_system(enemy_update_system)

'''
Immediate motion next step for A* calculating the velocity from the
enemy's current and next path index
'''
def calculate_velocity(p_pos: Vector2, e_pos: Vector2):

    delta = p_pos - e_pos

    if not delta:
        return delta
    
    velocity_x = Vector2(copysign(1.0, delta.x), 0)
    velocity_y = Vector2(0, copysign(1.0, delta.y))

    # If neither are in plane with player, choose random one
    if delta.x != 0 and delta.y != 0:
        return choice([velocity_x, velocity_y])

    if delta.x != 0:
        return velocity_x
    else:
        return velocity_y

def create_enemy(position = tuple[int, int]):
    enemy = Entity("enemy")
    enemy.enemy = EnemyComponent(damage = 10)
    enemy.sprite = SpriteComponent.from_resource("creatures/enemy.png")
    enemy.motion = MotionComponent(layer=motion.LAYER_ENEMIES, position = Vector2(position))
    enemy.health = HealthComponent(health = 100)
    enemy.sound = SoundComponent(sound_file='assets/sounds/enemy-move.mp3', volume=0.5, state=-1)

    return enemy


COST_MAPPING = {
    tilemap.TILE_EARTH: 1,
    tilemap.TILE_WATER: 3,
    tilemap.TILE_MUD:   2,
    tilemap.TILE_PLANT: 2,
    tilemap.TILE_EMBER: 3.
}

'''
Calculating cost of individual tile for A*
'''
def get_cost(value):
    return COST_MAPPING.get(value, 5)  # Default to infinity for unrecognized values

'''
Heuristic function (Manhattan distance for grid)
'''
def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

'''
A* algorithm implementation including. Returns next immediate velocity for enemy to take
'''
def a_star(map, e_pos, p_pos):

    frontier = PriorityQueue()
    frontier.put((0, e_pos))  # Priority queue stores (priority, node)
    
    came_from = {}
    cost_so_far = {}
    
    came_from[e_pos] = None
    cost_so_far[e_pos] = 0
    
    while not frontier.empty():
        _, current = frontier.get()
        
        if current == p_pos:
            break
        
        # Define the possible moves (up, down, left, right)
        neighbors = [
            (current[0] + 1, current[1]),   # Right 
            (current[0] - 1, current[1]),   # Left
            (current[0], current[1] + 1),   # Down
            (current[0], current[1] - 1)    # Up
        ]
        
        for next in neighbors:
            # Check if next position is within grid bounds

            if 0 <= next[0] < len(map) and 0 <= next[1] < len(map[0]):
                # Calculate the cost to move to the neighbor
                # TODO: Check, this might be reversed
                next_x = int(next[0])
                next_y = int(next[1])
                new_cost = cost_so_far[current] + get_cost(map[next_y][next_x])
                
                # If the neighbor hasn't been visited or a cheaper path is found
                if next not in cost_so_far or new_cost < cost_so_far[next]:
                    cost_so_far[next] = new_cost
                    priority = new_cost + heuristic(p_pos, next)
                    frontier.put((priority, next))
                    came_from[next] = current
    
    # Reconstruct path
    path = []
    current = p_pos
    while current != e_pos:  # Trace the path back from goal to start
        path.append(current)
        current = came_from[current]
    path.append(e_pos)
    path.reverse()  # Reverse the path to start -> goal

    velocity = Vector2(0)

    # Because system uses last two path nodes for A* to calculate next immediate 
    # vector for enemy to take towards player, with paht[0] being the current position
    if(len(path)>= 2):
        velocity = calculate_velocity(Vector2(path[1]), Vector2(path[0]))
    
    return velocity  # Return the path and total cost