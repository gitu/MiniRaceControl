import os
import pygame
import time
import random
 

 
class pyscope :
    screen = None;
    
    def __init__(self):
        os.environ["SDL_FBDEV"] = "/dev/fb1"
        pygame.init() 
        
        size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        print "Framebuffer size: %d x %d" % (size[0], size[1])
        self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        # Clear the screen to start
        self.screen.fill((0, 0, 0))        
        # Initialise font support
        pygame.font.init()
        # Render the screen
        pygame.display.update()
 
    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."
 
    def test(self):
        # Fill the screen with red (255, 0, 0)
        red = (255, 0, 0)
        self.screen.fill(red)
        # Update the display
        pygame.display.update()
 
# Create an instance of the PyScope class
scope = pyscope()
scope.test()
time.sleep(10)
