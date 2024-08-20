from pygame import Vector2
import pygame
from engine.ecs import Entity, EntityGroup
from engine.window import Window
from systems.tilemap import TilemapComponent, parse_tile_map


def init(group: EntityGroup, _: Window):
    map = parse_tile_map('maps/game-map-natural.png')

    tilemap = Entity("tilemap")
    tilemap.tilemap = TilemapComponent.from_map(map)
    group.add(tilemap)

    pygame.mixer.music.load('assets/sounds/Retro_Forest_-_David_Fesliyan.mp3')
    pygame.mixer.music.set_volume(0.2)
    pygame.mixer.music.play(-1)

    pygame.font.init()