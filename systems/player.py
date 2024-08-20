from engine.ecs import Entity, EntityGroup, enumerate_component
from pygame import Vector2

from systems.sounds import SoundComponent
from systems.ui import UIComponent

from .sprites import SpriteComponent
from .motion import MotionComponent
from .controls import ControlComponent
from .health import HealthComponent
from . import turn
from . import motion


'''
Component class to store player specific information
'''
@enumerate_component("player")
class PlayerComponent():
    pass

def get_direction_command(actions: list[str]) -> Vector2 | None:
    mapping = {
        "up_start": Vector2(0,-1),
        "down_start": Vector2(0,1),
        "left_start": Vector2(-1,0),
        "right_start": Vector2(1,0),
    }
    for key in mapping:
        if key in actions:
            return mapping[key]
    return None

'''
The player update system:
Update the players velocity based on the controls
'''
def player_update_system(group: EntityGroup):

    t: turn.TurnComponent = group.query_singleton("turn").turn
    player = group.query_singleton('player', 'motion', 'health')
    health_bar = group.query_singleton('health', 'motion', 'ui')

    health_bar.ui.text = "Health: " + str(player.health.health)

    if t.state != turn.TURN_PLAYER:
        # Nothing we can do
        return
    
    if not player.health.is_alive:
        game = group.query_singleton('game').game
        game.state = game.STATE_GAME_OVER
        return

    controls: ControlComponent = group.query_singleton('controls').controls

    dir_command = get_direction_command(controls.actions)
    if dir_command:
        player.motion.velocity = dir_command
        t.waiting = False

    if "skip_start" in controls.actions:
        t.waiting = False

    if 'up_start' in controls.actions:
        player.sprite = SpriteComponent.from_resource("player/player_up.png")
    elif 'down_start' in controls.actions:
        player.sprite = SpriteComponent.from_resource("player/player_down.png")
    elif 'left_start' in controls.actions:
        player.sprite = SpriteComponent.from_resource("player/player_l.png")
    elif 'right_start' in controls.actions:
        player.sprite = SpriteComponent.from_resource("player/player_r.png")



'''
Adds the player character, and mounts systems for updating the player with the control inputs
'''
def mount_player_system(group: EntityGroup):
    player = Entity("player")
    player.player = PlayerComponent()
    player.motion = MotionComponent(layer=motion.LAYER_PLAYER, position=Vector2(128,128))
    player.sprite = SpriteComponent.from_resource("player/player_down.png")
    player.health = HealthComponent(health = 100)
    player.sound = SoundComponent(sound_file='assets/sounds/step.mp3', volume=0.5, state=-1)
    group.add(player)

    health_box = Entity("health_box")
    health_box.motion = MotionComponent(position=Vector2(10,90))
    health_box.ui = UIComponent(text="Health: " + str(player.health.health))
    # So, this will probably cause issues. Sue me.
    health_box.health = player.health
    group.add(health_box)

    group.mount_system(player_update_system)
