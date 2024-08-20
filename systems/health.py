from engine.ecs import Entity, EntityGroup, enumerate_component
from systems.motion import MotionComponent
from systems.sounds import SoundComponent

@enumerate_component("health")
class HealthComponent:
    health: int
    previous_health: int = 0
    is_alive: bool = True

'''
Update health system for 
'''
def update_health_system(group: EntityGroup):
    for e in group.query("health"):
        if e.health.health < e.health.previous_health:
            if e.contains('player'):
                hurt_sound = Entity('sound')
                hurt_sound.sound = SoundComponent(sound_file='assets/sounds/player-damage.mp3', volume=0.5, state=0, destroy_after_play=True)
                hurt_sound.motion = MotionComponent(position=e.motion.position)

                group.add(hurt_sound)

        e.health.previous_health = e.health.health
        if e.health.health <= 0:
            e.health.is_alive = False


'''
Mount health system
'''
def mount_health_system(group: EntityGroup):
    group.mount_system(update_health_system)
    pass

