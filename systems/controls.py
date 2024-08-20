from engine.ecs import Entity, EntityGroup, enumerate_component, factory

import pygame
from pygame import Vector2

from systems.motion import MotionComponent
from systems.sprites import CameraComponent
from systems.utils import round_vector

key_mapping = {
    pygame.K_w: ["up"],
    pygame.K_a: ["left"],
    pygame.K_s: ["down"],
    pygame.K_d: ["right"],
    pygame.K_SPACE: ["skip"],
    pygame.K_1: ["select_spell_1"],
    pygame.K_2: ["select_spell_2"],
    pygame.K_3: ["select_spell_3"],
    pygame.K_4: ["select_spell_4"],
    pygame.K_5: ["select_spell_5"],
    pygame.K_6: ["select_spell_6"],
    pygame.K_7: ["select_spell_7"],
    pygame.K_8: ["select_spell_8"],
    pygame.K_9: ["select_spell_9"],
    pygame.K_g: ["sound_test"],
}

'''
Component class to store decoded control inputs
'''
@enumerate_component("controls")
class ControlComponent():
    direction: Vector2 = factory(Vector2)
    actions: list[str] =  factory(list)
    mouse_position: Vector2 = factory(Vector2)
    mouse_camera_position: Vector2 = factory(Vector2)
    mouse_grid_position: Vector2 = factory(Vector2)

def update_action(past_actions: list[str], actions: list[str], action: str, enabled: bool):
    if enabled:
        actions.append(action)
        if not action in past_actions:
            actions.append(action + "_start")
    elif action in past_actions:
        actions.append(action + "_stop")

'''
The controls handling system:
Read inputs from the keyboard, and store them in the controls component
'''
def update_controls_system(group: EntityGroup):

    controls: ControlComponent = group.query_singleton('controls').controls
    past_actions = controls.actions
    controls.actions = []
    keys = pygame.key.get_pressed()

    for key in key_mapping:
        for action in key_mapping[key]:
            action_enabled = keys[key]
            update_action(past_actions, controls.actions, action, action_enabled)

    for button_number, button_pressed in enumerate(pygame.mouse.get_pressed()):
        action = f"mouse_{button_number}"
        update_action(past_actions, controls.actions, action, button_pressed)

    mouse_pos = pygame.mouse.get_pos()
    controls.mouse_position = Vector2(mouse_pos)
    camera_entity = group.query_singleton('camera', 'motion')
    camera: CameraComponent = camera_entity.camera
    motion: MotionComponent = camera_entity.motion

    offset, scale = camera.get_screenspace_transform(motion.position)
    controls.mouse_camera_position = (mouse_pos - offset) / scale
    controls.mouse_grid_position = round_vector(controls.mouse_camera_position)

    controls.direction = Vector2(
        int(keys[pygame.K_d]) - int(keys[pygame.K_a]),
        int(keys[pygame.K_s]) - int(keys[pygame.K_w])
    )

'''
Mounts the components and systems for reading controls
'''
def mount_control_system(group: EntityGroup):
    controls = Entity("controls")
    controls.controls = ControlComponent()
    group.add(controls)

    group.mount_system(update_controls_system)
