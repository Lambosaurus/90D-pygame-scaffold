import pygame
from engine.ecs import Entity, EntityGroup, enumerate_component
from systems.motion import MotionComponent


@enumerate_component("ui")
class UIComponent:
    identifier: str = None
    text: str

@enumerate_component("font")
class FontComponent:
    font: pygame.font.Font

def ui_update_system(group: EntityGroup):
    camera_surface = group.query_singleton('camera').camera.surface
    font: pygame.font.Font = group.query_singleton('font').font.font

    for ui_entity in group.query('ui', 'motion'):
        ui: UIComponent = ui_entity.ui
        motion: MotionComponent = ui_entity.motion

        camera_surface.blit(font.render(ui.text, True, (255,255,255)), motion.position)


def mount_ui_system(group: EntityGroup):
    pygame.font.init()

    font_entity = Entity("font")
    font_entity.font = FontComponent(font=pygame.font.SysFont('Comic Sans MS', 20))

    group.add(font_entity)

    group.mount_system(ui_update_system)