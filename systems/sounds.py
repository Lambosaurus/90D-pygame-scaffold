

import random
from pygame import Vector2
import pygame
from engine.ecs import Entity, EntityGroup, enumerate_component
from systems.controls import ControlComponent
from systems.motion import MotionComponent
from pygame import mixer

SOUND_AUDIBLE_DISTANCE = 80

@enumerate_component('sound')
class SoundComponent:
    STATE_IDLE = -1
    STATE_PLAY = 0
    STATE_PLAYING = 1
    STATE_STOPPED = 2

    sound_file: str
    volume: float = 1.0
    state: int = -1
    destroy_after_play: bool = False

def play_sound_system(group: EntityGroup):
    player_entity = group.query_singleton('player', 'motion')
    player_motion: MotionComponent = player_entity.motion
    controls: ControlComponent = group.query_singleton('controls').controls

    if 'sound_test_start' in controls.actions:
        test_sound = Entity('sound')
        test_sound.sound = SoundComponent(sound_file='assets/sounds/fire.mp3', volume=0.5, state=0)
        test_sound.motion = MotionComponent(position=player_motion.position + Vector2(20, 20) * random.random())

        group.add(test_sound)

    for entity in group.query('sound', 'motion'):
        sound: SoundComponent = entity.sound
        motion: MotionComponent = entity.motion

        if sound.state == SoundComponent.STATE_PLAY:
            sound.state = SoundComponent.STATE_PLAYING
            distance = player_motion.position.distance_to(motion.position)
            if distance < SOUND_AUDIBLE_DISTANCE:
                sound.state = SoundComponent.STATE_STOPPED
                sound_file = pygame.mixer.Sound(sound.sound_file)
                sound_file.set_volume(sound.volume * (1 - distance / SOUND_AUDIBLE_DISTANCE))
                sound_file.play(0, 2000)
            if sound.destroy_after_play:
                group.remove(entity)

def create_sound(sound_file: str, volume: float = 1.0, position = Vector2(0, 0)):
    sound_entity = Entity('sound')
    sound_entity.sound = SoundComponent(sound_file, volume)
    sound_entity.motion = MotionComponent(position)

def mount_sound_system(group: EntityGroup):
    mixer.init()

    group.mount_system(play_sound_system)