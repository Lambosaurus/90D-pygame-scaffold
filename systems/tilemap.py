from typing import Union
from pygame import Color, Vector2, image, Rect
from engine.assets import AssetPipeline
from engine.ecs import enumerate_component, factory

TILE_EARTH = 0
TILE_WATER = 1
TILE_MUD = 2
TILE_PLANT = 3
TILE_EMBER = 4
TILE_ICE = 5
TILE_ROCK = 6
TILE_LAVA = 7
TILE_HELLSCAPE = 8
TILE_ASH = 9
TILE_MARSH = 10
TILE_OOZE = 11
TILE_BONES = 12

type Tilemap = list[list[int]]
# We may want to make this a literal and/or use an enum
type Tile = int

def rgb_key(rgba: tuple[int, int, int, int]):
    key = ''
    for part in rgba:
        key += '_' + str(part)

    return key

TILE_COLOR_MAP = {
    rgb_key(Color('#67584b')): TILE_EARTH,
    rgb_key(Color('#4772e5')): TILE_WATER,
    rgb_key(Color('#5d330e')): TILE_MUD,
    rgb_key(Color('#6ad127')): TILE_PLANT,
    rgb_key(Color('#e04a09')): TILE_EMBER,
    rgb_key(Color('#c5d5ff')): TILE_ICE,
    rgb_key(Color('#9fa2aa')): TILE_ROCK,
    rgb_key(Color('#df4a00')): TILE_LAVA,
    rgb_key(Color('#56001a')): TILE_HELLSCAPE,
    rgb_key(Color('#46403a')): TILE_ASH,
    rgb_key(Color('#762981')): TILE_MARSH,
    rgb_key(Color('#d30b91')): TILE_OOZE,
}

asset_pipeline = AssetPipeline.get_instance()

TILE_SPRITES = {
    TILE_EARTH: asset_pipeline.get_image('tiles/earth.png'),
    TILE_WATER: asset_pipeline.get_image('tiles/water.png'),
    TILE_MUD: asset_pipeline.get_image('tiles/mud.png'),
    TILE_PLANT: asset_pipeline.get_image('tiles/plant.png'),
    TILE_EMBER: asset_pipeline.get_image('tiles/ember.png'),
    TILE_ASH: asset_pipeline.get_image('tiles/ash.png'),
    TILE_HELLSCAPE: asset_pipeline.get_image('tiles/hellscape.png'),
    TILE_ICE: asset_pipeline.get_image('tiles/ice.png'),
    TILE_LAVA: asset_pipeline.get_image('tiles/lava.png'),
    TILE_MARSH: asset_pipeline.get_image('tiles/marsh.png'),
    TILE_OOZE: asset_pipeline.get_image('tiles/ooze.png'),
    TILE_ROCK: asset_pipeline.get_image('tiles/rock.png'),
}

'''
Component that stores a tilemap
'''
@enumerate_component("tilemap")
class TilemapComponent():
    bounds: Rect
    map: list[list[int]]

    def get_tile(self, coord: Union[Vector2, tuple[int, int]]):
        if not self.contains(coord):
            return None
        
        return self.map[int(coord[1])][int(coord[0])]
    
    def set_tile(self, coord: Union[Vector2, tuple[int, int]], tile: Tile):
        if not self.contains(coord):
            return

        self.map[int(coord[1])][int(coord[0])] = tile

    def contains(self, coord: Union[Vector2, tuple[int, int]]):
        return self.bounds.contains(coord, (0, 0))

    @staticmethod
    def from_map(map: Tilemap):
        bounds = Rect(0, 0, 0, 0)
        bounds.center = (0, 0)

        return TilemapComponent(
            map = map,
            bounds = bounds
        )


def parse_tile_map(image_path: str) -> Tilemap:
    map_surface = AssetPipeline.get_instance().get_image(image_path)
    map: Tilemap = list()
    for y in range(map_surface.get_height()):
        map.append(list())
        for x in range(map_surface.get_width()):
            tile_color = rgb_key(map_surface.get_at((x, y)))
            tile = TILE_COLOR_MAP.get(tile_color) or TILE_EARTH
            map[y].append(tile)
    
    return map
