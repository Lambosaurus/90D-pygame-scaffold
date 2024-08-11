from engine.entity import Entity, EntityGroup
from engine.window import Window

import pygame


'''
Dataclass to contain decoded input information
'''
class ControlComponent():
    def __init__(self):
        self.direction: tuple[int,int] = (0,0)
    
def _get_direction_control(keys) -> tuple[int,int]:
    dir = [0,0]
    if keys[pygame.K_w]:
        dir[1] -= 1
    if keys[pygame.K_s]:
        dir[1] += 1
    if keys[pygame.K_a]:
        dir[0] -= 1
    if keys[pygame.K_d]:
        dir[0] += 1
    return dir

'''
The controls handling system:
Read inputs from the keyboard, and store them in the controls component
'''
def update_controls_system(group: EntityGroup):
    controls: ControlComponent = group.query_singleton('controls').controls
    keys = pygame.key.get_pressed()
    controls.direction = _get_direction_control(keys)

'''
Mounts the components and systems for reading controls
'''
def mount_control_system(group: EntityGroup, window: Window):
    controls = group.create()
    controls.controls = ControlComponent()
    
    group.mount_system(update_controls_system)
