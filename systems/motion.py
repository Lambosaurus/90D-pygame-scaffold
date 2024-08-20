from enum import Enum
from engine.ecs import EntityGroup, enumerate_component, factory
from pygame import Vector2

from .turn import TurnComponent
from .tilemap import TilemapComponent
#from .collision import CollisionComponent
from . import utils

LAYER_NONE = None
LAYER_PLAYER = 0
LAYER_ENEMIES = 1
LAYER_EFFECTS = 2
LAYER_COUNT = 3

class Direction:
    UP = Vector2(0, -1)
    DOWN = Vector2(0, 1)
    LEFT = Vector2(-1, 0)
    RIGHT = Vector2(1, 0)

'''
Component containing a position, velocity, ect
'''
@enumerate_component("motion")
class MotionComponent():
    position: Vector2 = factory(Vector2)
    velocity: Vector2 = factory(Vector2)
    layer: int | None = LAYER_NONE

'''
The motion update system:
Update any entities with motions components
'''
def motion_update_system(group: EntityGroup):

    t: TurnComponent = group.query_singleton('turn').turn
    if t.waiting:
        return
    
    tilemap: TilemapComponent = group.query_singleton("tilemap").tilemap
    collision = group.query_singleton("collision").collision

    # Update the position of all entities with a velocity
    for e in group.query('motion'):
        motion: MotionComponent = e.motion
        if motion.velocity:
            new_position = motion.position + motion.velocity
            if tilemap.contains(new_position) and not collision.is_occupied(new_position, motion.layer):
                motion.position = new_position
            motion.velocity = Vector2(0)

'''
Mounts systems for updating motion components
'''
def mount_motion_system(group: EntityGroup):
    group.mount_system(motion_update_system)

