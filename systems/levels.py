import random
from pygame import Rect, Surface, Vector2
from engine.ecs import Entity, EntityGroup, enumerate_component, factory
from systems.controls import ControlComponent
from systems.enemy import create_enemy
from systems.motion import Direction, MotionComponent
from systems.sprites import CameraComponent
from systems.tilemap import TilemapComponent
from systems.turn import TURN_PLAYER, TurnComponent
from systems.ui import UIComponent
from systems.utils import round_vector


ENEMY_TYPES = {
    'mook': create_enemy((0, 0)),
    'boss': create_enemy((0, 0))
}


LEVELS = {
    1: {
        'spawn_area': (67, 56, 5, 5),  # x, y, length, width
        'enemies': {
            'mook': 5,
            'boss': 1
        },
        'map_bounds': (16, 16)
    },
    2: {
        'spawn_area': (53, 53, 5, 5),
        'enemies': {
            'mook': 10,
            'boss': 4
        },
        'map_bounds': (22, 22)
    },
    3: {
        'spawn_area': (51, 51, 4, 4),
        'enemies': {
            'mook': 20,
            'boss': 8
        },
        'map_bounds': (27, 27)
    },
    4: {
        'spawn_area': (81, 81, 12, 12),
        'enemies': {
            'mook': 30,
            'boss': 16
        },
        'map_bounds': (35, 35)
    },
    5: {
        'spawn_area': (86, 86, 35, 35),
        'enemies': {
            'mook': 50,
            'boss': 32
        },
        'map_bounds': (45, 45)
    },
    6: {
        'spawn_area': (69, 69, 42, 42),
        'enemies': {
            'mook': 80,
            'boss': 32
        },
        'map_bounds': (58, 58)
    },
    7: {
        'spawn_area': (56, 56, 42, 42),
        'enemies': {
            'mook': 120,
            'boss': 32
        },
        'map_bounds': (72, 72)
    },
    8: {
        'spawn_area': (35, 35, 42, 42),
        'enemies': {
            'mook': 160,
            'boss': 32
        },
        'map_bounds': (93, 93)
    },
    9: {
        'spawn_area': (0, 0, 128, 128),
        'enemies': {
            'mook': 200,
            'boss': 32
        },
        'map_bounds': (128, 128)
    },
    10: {
        'spawn_area': (0, 0, 128, 128),
        'enemies': {
            'mook': 300,
            'boss': 32
        },
        'map_bounds': (128, 128)
    }
}

@enumerate_component('level')
class LevelComponent:
    current_level: int = 0
    levels: dict = factory(LEVELS)
    map: str = 'maps/map.png'


@enumerate_component('spawn')
class EnemySpawnComponent:
    enemy_type: str
    count: int = None
    interval: float = None
    last_spawned_turn: int = 0
    area: Rect = None

@enumerate_component('game')
class GameComponent:
    STATE_START_SCREEN = 0
    STATE_PLAYING = 1
    STATE_GAME_OVER = 2
    STATE_WIN = 3

    state: int = 0

def level_progression_system(group: EntityGroup):
    game: GameComponent = group.query_singleton('game').game
    if game.state != game.STATE_PLAYING:
        return

    enemy_entities = group.query('enemy')
    spawn_entities = group.query('spawn')
    level_entity = group.query_singleton('level', 'ui')
    level: LevelComponent = level_entity.level
    ui: UIComponent = level_entity.ui
    enemies = list(enemy_entities)
    spawns = list(spawn_entities)
    unspawned_enemies_count = sum([spawn.spawn.count for spawn in spawns])

    ui.text = f'Level {level.current_level}, enemies: {len(enemies)}, unspawned: {unspawned_enemies_count}'

    if len(enemies) <= 0 and unspawned_enemies_count <= 0:
        level.current_level += 1
        level_config = level.levels.get(level.current_level)
        if not level_config == None:
            map: TilemapComponent = group.query_singleton('tilemap').tilemap
            map.bounds = Rect(Vector2(len(map.map))/2 - Vector2(level_config['map_bounds']) / 2, level_config['map_bounds'])
            spawn_area = Rect(level_config['spawn_area'])
            spawn_interval = level_config.get('spawn_interval', 5)
            for enemy_type, count in level_config['enemies'].items():
                spawn = Entity('spawn')
                spawn.spawn = EnemySpawnComponent(enemy_type=enemy_type, count=count, interval=spawn_interval, area=spawn_area)
                spawn.motion = MotionComponent(position=spawn_area.topleft)
                group.add(spawn)
        else:
            print('Game Over. You win!')

def spawn_enemy_system(group: EntityGroup):
    turn: TurnComponent = group.query_singleton('turn').turn

    spawn_entities = group.query('spawn', 'motion')
    for spawn_entity in spawn_entities:
        spawn: EnemySpawnComponent = spawn_entity.spawn
        spawn_area = spawn.area

        if spawn.count <= 0:
            group.remove(spawn_entity)
            continue

        if turn.number - spawn.last_spawned_turn < spawn.interval:
            continue


        random_spawn = round_vector(Vector2(spawn_area.topleft) + Vector2(spawn_area.size) * random.random())
        spawn.last_spawned_turn = turn.number
        spawn.count -= 1
        enemy = ENEMY_TYPES.get(spawn.enemy_type).clone()
        enemy.motion.position = Vector2(random_spawn)
        group.add(enemy)

def game_state_system(group: EntityGroup):
    game_entity = group.query_singleton('game', 'ui')
    game: GameComponent = game_entity.game
    controls: ControlComponent = group.query_singleton('controls').controls

    if game.state == game.STATE_START_SCREEN:
        if len(controls.actions) > 0:    
            game.state = game.STATE_PLAYING
            game_entity.ui.text = ''

    elif game.state == game.STATE_GAME_OVER:
        camera: CameraComponent = group.query_singleton('camera').camera
        camera_surface = camera.surface

        game_over = Entity('game_over')
        game_over.ui = UIComponent(text='Game Over')
        game_over.motion = MotionComponent(position=camera_surface.get_rect().center - Vector2(50, 0))
        group.add(game_over)


    elif game.state == game.STATE_WIN:
        camera: CameraComponent = group.query_singleton('camera').camera
        camera_surface = camera.surface

        game_over = Entity('you_win')
        game_over.ui = UIComponent(text='You win!')
        game_over.motion = MotionComponent(position=camera_surface.get_rect().center - Vector2(50, 0))
        group.add(game_over)
    

def mount_level_system(group: EntityGroup, surface: Surface):
    game_entity = Entity('game')
    game_entity.game = GameComponent()
    game_entity.motion = MotionComponent(position=surface.get_rect().center - Vector2(100, 0))
    game_entity.ui = UIComponent(text='Press any key to start')

    group.add(game_entity)

    level_entity = Entity('levels')
    level_entity.level = LevelComponent(levels=LEVELS)
    level_entity.ui = UIComponent(text='')
    level_entity.motion = MotionComponent(position=Vector2(10, 10))

    group.add(level_entity)

    group.mount_system(game_state_system)
    group.mount_system(level_progression_system)
    group.mount_system(spawn_enemy_system)

