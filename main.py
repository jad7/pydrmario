import pygame
from pygame import DOUBLEBUF, RESIZABLE, SCALED
from pygame.locals import (
    KEYDOWN,
    QUIT,
)

from bottle import Bottle
from brick import init as viruses_init
from constants import BLACK
from pillow import Pillow

X = 8
Y = 17

pygame.font.init()

bottle_offset = (200, 100)
brick_size = 40
virus_offset = 5
VIRUSES_COUNT = 84
bottle: Bottle = None
next_pillow_offset = (bottle_offset[0] + X * brick_size + 20, 10)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 1000

# Create the screen object
# The size is determined by the constant SCREEN_WIDTH and SCREEN_HEIGHT
# screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), SCALED | RESIZABLE | DOUBLEBUF)
# screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT),HWSURFACE|DOUBLEBUF|RESIZABLE)
# fake_screen = screen.copy()
viruses_init()

tick = 2 * 3
mult = 1

running = True

pause_state = None
state = -1
next_pillow = None
pillow = None
falled = set()
clock = pygame.time.Clock()
# Main loop
num = 0
# pygame.key.set_repeat(200, 200)
while running:
    mult = 1
    # resize_events = pygame.event.get(eventtype=VIDEORESIZE)
    # if resize_events:
    #    screen = pygame.display.set_mode(resize_events[0].size, HWSURFACE | DOUBLEBUF | RESIZABLE)

    quit_events = pygame.event.get(eventtype=QUIT)
    if quit_events:
        running = False

    events_raw = pygame.event.get(eventtype=KEYDOWN)
    keys = {event.key: event for event in events_raw}

    if state == -1:
        if bottle:
            bottle.empty()
        bottle = Bottle(X, Y, brick_size, offset=bottle_offset)
        pillow = None
        next_pillow = None
        bottle.populate_viruses(VIRUSES_COUNT, virus_offset)
        state = 0

    if bottle.virus_count() == 0:
        state = 5

    if state == 0:
        if next_pillow is None:
            next_pillow = Pillow.create(brick_size, next_pillow_offset)
            bottle.add(*next_pillow.bricks())
        pillow = bottle.add_pillow(next_pillow)
        next_pillow = Pillow.create(brick_size, next_pillow_offset)
        bottle.add(*next_pillow.bricks())
        state = 1
    elif state == 1:
        # Moving the paddle when the use uses the arrow keys
        downkeys = pygame.key.get_pressed()
        # downkeys = pygame.event.get(eventtype=KEYDOWN)
        if pygame.K_q in keys:
            tick = tick + 1
        if pygame.K_w in keys:
            tick = tick - 1
        if pygame.K_LEFT in keys:
            pillow.move_left()
        if pygame.K_RIGHT in keys:
            pillow.move_right()
        if downkeys[pygame.K_DOWN]:
            mult = 4
        if pygame.K_z in keys:
            pillow.turn_uclw()
        if pygame.K_x in keys:
            pillow.turn_clw()
        if pygame.K_RETURN in keys:
            bottle.pause()
            pause_state = state
            state = 6

        num = (num + 1) % 3
        if num == 0:
            if not pillow.move_down():
                state = 2

    elif state == 2:
        if bottle.burn(pillow):
            state = 3
        else:
            state = 0

    elif state == 3:
        res = bottle.fallout()
        if not res:
            state = 4
        else:
            falled.update(res)

    elif state == 4:
        if bottle.burn(*falled):
            state = 3
        else:
            state = 0
        falled.clear()

    elif state == 5:
        bottle.end()
        if keys:
            if pygame.K_RETURN in keys:
                state = -1
    elif state == 6:
        if pygame.K_RETURN in keys:
            state = pause_state
            bottle.unpause()

    bottle.update()
    screen.fill(BLACK)
    # Now let's draw all the sprites in one go. (For now we only have 2 sprites!)
    bottle.draw(screen)
    # screen.blit(pygame.transform.scale(screen, screen.get_rect().size), (0, 0))
    pygame.display.flip()
    # --- Go ahead and update the screen with what we've drawn.
    pygame.display.flip()

    # --- Limit to 60 frames per second
    clock.tick(tick * mult)

pygame.quit()
