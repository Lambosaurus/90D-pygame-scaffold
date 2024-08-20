import pygame

class Window():

    '''
    Initialize a pygame window and rendering target.
    '''
    def __init__(self, res: tuple[int,int] = (1280,800), name: str = "ECS engine"):
        pygame.init()
        pygame.display.set_caption(name)
        self.surface = pygame.display.set_mode(res, pygame.RESIZABLE)
        self.surface.fill((0,0,0))
        self.clock = pygame.time.Clock()
        self.frame_rate = 60
        self.exited = False

    '''
    Handle the pygame event queue
    '''
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.exited = True

    '''
    Update the display (assuming the render surface has been modified).
    Also introduces a delay to maintain the desired frame rate.
    '''
    def update(self):
        pygame.display.flip()
        self.clock.tick(self.frame_rate)
        self.surface.fill((0,0,0))

    def close(self):
        pygame.quit()


