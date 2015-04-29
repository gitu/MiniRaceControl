# Based on cam.py by Phil Burgess / Paint Your Dragon for Adafruit Industries.
# BSD license, all text above must be included in any redistribution.

import fnmatch
import os
import os.path
import sys

import pygame
from pygame.locals import *



# UI classes ---------------------------------------------------------------

# Small resistive touchscreen is best suited to simple tap interactions.
# Importing a big widget library seemed a bit overkill.  Instead, a couple
# of rudimentary classes are sufficient for the UI elements:

# Icon is a very simple bitmap class, just associates a name and a pygame
# image (PNG loaded from icons directory) for each.
# There isn't a globally-declared fixed list of Icons.  Instead, the list
# is populated at runtime from the contents of the 'icons' directory.
from ConnectCarrera import RaceTrackImpl
from RaceManager import RaceManager
import settings


class Icon:
    def __init__(self, name):
        self.name = name
        try:
            self.bitmap = pygame.image.load(iconPath + '/' + name + '.png')
        except:
            pass


# Button is a simple tappable screen region.  Each has:
#  - bounding rect ((X,Y,W,H) in pixels)
#  - optional background color and/or Icon (or None), always centered
#  - optional foreground Icon, always centered
#  - optional single callback function
#  - optional single value passed to callback
# Occasionally Buttons are used as a convenience for positioning Icons
# but the taps are ignored.  Stacking order is important; when Buttons
# overlap, lowest/first Button in list takes precedence when processing
# input, and highest/last Button is drawn atop prior Button(s).  This is
# used, for example, to center an Icon by creating a passive Button the
# width of the full screen, but with other buttons left or right that
# may take input precedence (e.g. the Effect labels & buttons).
# After Icons are loaded at runtime, a pass is made through the global
# buttons[] list to assign the Icon objects (from names) to each Button.

class Button:
    def __init__(self, rect, **kwargs):
        self.rect = rect  # Bounds
        self.color = None  # Background fill color, if any
        self.iconBg = None  # Background Icon (atop color fill)
        self.iconFg = None  # Foreground Icon (atop background)
        self.bg = None  # Background Icon name
        self.fg = None  # Foreground Icon name
        self.callback = None  # Callback function
        self.value = None  # Value passed to callback
        for key, value in kwargs.iteritems():
            if key == 'color':
                self.color = value
            elif key == 'bg':
                self.bg = value
            elif key == 'fg':
                self.fg = value
            elif key == 'cb':
                self.callback = value
            elif key == 'value':
                self.value = value

    def selected(self, position):
        x1 = self.rect[0]
        y1 = self.rect[1]
        x2 = x1 + self.rect[2] - 1
        y2 = y1 + self.rect[3] - 1
        if ((position[0] >= x1) and (position[0] <= x2) and
                (position[1] >= y1) and (position[1] <= y2)):
            if self.callback:
                if self.value is None:
                    self.callback()
                else:
                    self.callback(self.value)
            return True
        return False

    def draw(self, target_screen):
        if self.color:
            target_screen.fill(self.color, self.rect)
        if self.iconBg:
            target_screen.blit(self.iconBg.bitmap,
                               (self.rect[0] + (self.rect[2] - self.iconBg.bitmap.get_width()) / 2,
                                self.rect[1] + (self.rect[3] - self.iconBg.bitmap.get_height()) / 2))
        if self.iconFg:
            target_screen.blit(self.iconFg.bitmap,
                               (self.rect[0] + (self.rect[2] - self.iconFg.bitmap.get_width()) / 2,
                                self.rect[1] + (self.rect[3] - self.iconFg.bitmap.get_height()) / 2))

    def set_bg(self, name):
        if name is None:
            self.iconBg = None
        else:
            for icon in icons:
                if name == icon.name:
                    self.iconBg = icon
                    break


# UI callbacks -------------------------------------------------------------
# These are defined before globals because they're referenced by items in
# the global buttons[] list.

def quit_callback():  # Quit confirmation button
    raise SystemExit


def setting_callback(n):  # Pass 1 (next setting) or -1 (prev setting)
    global screenMode
    screenMode += n
    if screenMode < 0:
        screenMode = len(buttons) - 1
    elif screenMode >= len(buttons):
        screenMode = 0


# Global stuff -------------------------------------------------------------

screenMode = 0  # Current screen mode; default = viewfinder
screenModePrior = -1  # Prior screen mode (for detecting changes)
race_state_counter_prior = -1  # Prior race state id mode (for detecting changes)
iconPath = 'icons'  # Subdirectory containing UI bitmaps (PNG format)
saveIdx = -1  # Image index for saving (-1 = none set yet)
loadIdx = -1  # Image index for loading
scaled = None  # pygame Surface w/last-loaded image

icons = []  # This list gets populated at startup

pygame.font.init()
myfont = pygame.font.SysFont("monospace", 36)

buttons = [
    [Button((0, 0, 80, 52), bg='prev', cb=setting_callback, value=-1),
     Button((400, 0, 80, 52), bg='next', cb=setting_callback, value=1),
     Button((0, 10, 480, 35), bg='stats')],
    [Button((0, 0, 80, 52), bg='prev', cb=setting_callback, value=-1),
     Button((400, 0, 80, 52), bg='next', cb=setting_callback, value=1),
     Button((0, 10, 480, 35), bg='console')],
    [Button((0, 0, 80, 52), bg='prev', cb=setting_callback, value=-1),
     Button((400, 0, 80, 52), bg='next', cb=setting_callback, value=1),
     Button((190, 80, 100, 120), bg='quit-ok', cb=quit_callback),
     Button((0, 10, 480, 35), bg='quit')]
]


# Initialization -----------------------------------------------------------

# Init framebuffer/touchscreen environment variables
os.putenv('SDL_VIDEODRIVER', 'fbcon')
os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

# Get user & group IDs for file & folder creation
# (Want these to be 'pi' or other user, not root)
s = os.getenv("SUDO_UID")
uid = int(s) if s else os.getuid()
s = os.getenv("SUDO_GID")
gid = int(s) if s else os.getgid()

send_to_fb = len(sys.argv) > 1 and sys.argv[1] == "true"

print("init")

# Init pygame and screen
pygame.init()
pygame.mouse.set_visible(False)
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

print "Loading Icons..."
# Load all icons at startup.
for icon_file in os.listdir(iconPath):
    if fnmatch.fnmatch(icon_file, '*.png'):
        icons.append(Icon(icon_file.split('.')[0]))

# Assign Icons to Buttons, now that they're loaded
print "Assigning Buttons"
for s in buttons:  # For each screenful of buttons...
    for b in s:  # For each button on screen...
        for i in icons:  # For each icon...
            if b.bg == i.name:  # Compare names; match?
                b.iconBg = i  # Assign Icon to Button
                b.bg = None  # Name no longer used; allow garbage collection
            if b.fg == i.name:
                b.iconFg = i
                b.fg = None

print "loading background.."
img = pygame.image.load("images/bg.png")


print "init Race Manager"
race_manager = RaceManager(RaceTrackImpl(settings.serial_port), send_to_fb)


# Main loop ----------------------------------------------------------------

while True:
    # Process touchscreen input
    while True:
        screen_change = 0
        for event in pygame.event.get():
            if event.type is MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for b in buttons[screenMode]:
                    if b.selected(pos):
                        break
                screen_change = 1

        if race_manager.race_state_counter != race_state_counter_prior:
            race_state_counter_prior = race_manager.race_state_counter
            break
        if screen_change == 1 or screenMode != screenModePrior:
            break

    if img is None:  # clear background
        screen.fill(0)
    if img:
        screen.blit(img,
                    ((480 - img.get_width()) / 2,
                     (320 - img.get_height()) / 2))

    # Overlay buttons on display and update
    for i, b in enumerate(buttons[screenMode]):
        b.draw(screen)

    if screenMode == 0:
        for idx, result in enumerate(race_manager.rounds[::-1]):
            try:
                text = myfont.render('car ' + str(result['car']) + ' - ' + "{:7.3f}".format(result['time'] / 1000.0) + 's', 1, (10, 10, 10))
                text_pos = text.get_rect()
                text_pos.centerx = screen.get_rect().centerx
                text_pos.top = idx * myfont.get_linesize() + 80
                screen.blit(text, text_pos)
                if idx > 3:
                    break
            except IndexError:
                print("too long time")

    if screenMode == 1:
        idx = 0

        for key, car in race_manager.cars.iteritems():
            try:
                text = myfont.render('car ' + str(car['car']) + ' - ' + str(car['rounds']) + ' - ' + "{:7.3f}".format(car['fastest'] / 1000.0) + 's', 1, (10, 10, 10))
                text_pos = text.get_rect()
                text_pos.centerx = screen.get_rect().centerx
                text_pos.top = idx * myfont.gyet_linesize() + 80
                screen.blit(text, text_pos)
                idx += 1
                if idx > 3:
                    break
            except IndexError:
                print("too long time")


    pygame.display.update()
    screenModePrior = screenMode

