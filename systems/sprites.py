from engine.assets import AssetPipeline
from engine.ecs import Entity, EntityGroup, enumerate_component
import os
import math

import pygame
from pygame.surface import Surface
from pygame import Color, Vector2

from systems.tilemap import TILE_SPRITES, TilemapComponent

from .motion import MotionComponent



'''
A component that contains sprite information
'''
@enumerate_component("sprite")
class SpriteComponent():
    surface: Surface

    '''
    Creates a sprite from a resource file
    '''
    @staticmethod
    def from_resource(resource: str) -> 'SpriteComponent':
        asset_pipeline = AssetPipeline.get_instance()
        surface = asset_pipeline.get_image(resource)
        return SpriteComponent(surface=surface)

    '''
    Creates a filled square as a sprite
    '''
    @staticmethod
    def from_box(size: tuple[int,int], color: tuple[int,int,int]):
        surface = Surface(size)
        surface.fill(color)
        return SpriteComponent(surface=surface)

    '''
    Creates a filled circle as a sprite
    '''
    @staticmethod
    def from_circle(diameter: int, color: tuple[int,int,int]):
        surface = Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(surface, color, Vector2(diameter/2), diameter/2)
        return SpriteComponent(surface=surface)


TILE_SCALE = 32

'''
A component that represents a camera
'''
@enumerate_component("camera")
class CameraComponent():
    surface: Surface
    scale: float = TILE_SCALE

    def get_screenspace_transform(self, pos: Vector2) -> tuple[Vector2, float]:
        screen_center = Vector2(self.surface.get_size()) / 2
        return (screen_center - (pos * self.scale), self.scale)

'''
The sprite drawings system:
Use the camera position to draw all entities with a sprite at their relative location.
'''
def draw_sprite_system(group: EntityGroup):

    camera = group.query_singleton('camera', 'motion')
    tilemap: TilemapComponent = group.query_singleton('tilemap').tilemap
    
    surface: Surface = camera.camera.surface
    offset, scale = camera.camera.get_screenspace_transform(camera.motion.position)

    asset_pipeline = AssetPipeline.get_instance()
    tile_size = Vector2(math.ceil(scale))
    scaled_sprites = {key: pygame.transform.scale(sprite, tile_size) for key, sprite in TILE_SPRITES.items()}
    unknown_sprite = pygame.transform.scale(asset_pipeline.get_image('tiles/unknown.png'), tile_size)

    
    tile_center = Vector2(scale / 2)
    for y in range(tilemap.bounds.left, tilemap.bounds.right):
        for x in range(tilemap.bounds.top, tilemap.bounds.bottom):
            tile = tilemap.get_tile((x,y))
            scaled_sprite = scaled_sprites.get(tile) or unknown_sprite
            screen_pos = Vector2(x,y) * scale + offset
            surface.blit(scaled_sprite, screen_pos - tile_center)

    for e in sorted((e for e in group.query('sprite', 'motion') if (e.motion.layer != None)), key = lambda e: -e.motion.layer):
        
        motion: MotionComponent = e.motion
        sprite: SpriteComponent = e.sprite
        
        scaled_sprite = pygame.transform.scale_by(sprite.surface, scale / TILE_SCALE)
        screen_pos = motion.position * scale + offset
        sprite_center = Vector2(scaled_sprite.get_size())/2

        # Note, we are ignoring any screen-space culling
        surface.blit(scaled_sprite, screen_pos - sprite_center)

def camera_update_system(group: EntityGroup):
    camera_entity = group.query_singleton('camera', 'motion')
    camera_motion: MotionComponent = camera_entity.motion
    camera: CameraComponent = camera_entity.camera
    tilemap: TilemapComponent = group.query_singleton('tilemap').tilemap
    if not tilemap:
        return

    camera_motion.position = tilemap.bounds.topleft + (Vector2(tilemap.bounds.width) - Vector2(1)) / 2
    scale_size = min(camera.surface.get_width(), camera.surface.get_height())
    camera.scale = scale_size if tilemap.bounds.width == 0 else scale_size / tilemap.bounds.width

    

'''
Mounts the sprite drawing system, and adds a camera component for the viewport
'''
def mount_sprite_system(group: EntityGroup, target: Surface):
    camera = Entity("camera")
    camera.camera = CameraComponent(surface=target)
    camera.motion = MotionComponent(position=Vector2(0,0))
    group.add(camera)

    group.mount_system(camera_update_system)
    group.mount_system(draw_sprite_system)

