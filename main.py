import pygame
from pygame import DOUBLEBUF, RESIZABLE, SCALED
from pygame.locals import (
    KEYDOWN,
    QUIT,
)

from constants import BLACK, GREEN
from objects.bottle import Bottle
from objects.brick import init as viruses_init
from objects.pillow import Pillow

X = 8
Y = 17
between_bricks = 3
pygame.font.init()

bottle_offset = (50, 50)
brick_size = 20
virus_offset = 5
VIRUSES_COUNT = 84
bottle: Bottle = None
next_pillow_offset = (bottle_offset[0] + X * brick_size + 20, 10)

SCREEN_WIDTH = 300
SCREEN_HEIGHT = 450

# Create the screen object
# The size is determined by the constant SCREEN_WIDTH and SCREEN_HEIGHT
# screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), SCALED | RESIZABLE | DOUBLEBUF)
# screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT),HWSURFACE|DOUBLEBUF|RESIZABLE)
# fake_screen = screen.copy()
bg_cube_size = 10
for i in range(SCREEN_WIDTH // bg_cube_size - 1):
    for j in range(SCREEN_HEIGHT // bg_cube_size - 1):
        color = GREEN if (i + j) % 2 == 0 else BLACK
        pygame.draw.rect(screen, color,
                         [i * bg_cube_size, j * bg_cube_size, (i + 1) * bg_cube_size, (j + 1) * bg_cube_size])

# Y-1 because position 0 is reserved, by out-of-box
bottle_surf = screen.subsurface([bottle_offset[0], bottle_offset[1], (X * (brick_size + between_bricks)),
                                 ((Y - 1) * (brick_size + between_bricks))])
bottle_surf.fill(BLACK)

next_pillow_surf = screen.subsurface(
    [bottle_offset[0] + X * brick_size + 20, 10, brick_size * 2 + between_bricks, brick_size])
pygame.draw.rect(screen, BLACK,
                 [bottle_offset[0] + X * brick_size + 20 - 10, 10 - 10, brick_size * 2 + between_bricks + 20,
                  brick_size + 20])
# next_pillow_surf.fill(BLACK)
# bottle_surf = screen.subsurface(0, 0, )


viruses_init()

tick = 1 * 3
mult = 1

running = True

pause_state = None
state = -1
next_pillow = None
pillow = None
falled = set()
clock = pygame.time.Clock()
delay_before_start = 10
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
        bottle = Bottle(X, Y, brick_size, bottle_surf)
        pillow = None
        next_pillow = Pillow.create(brick_size, [0, 0])
        bottle.populate_viruses(VIRUSES_COUNT, virus_offset)
        state = -2

    if bottle.virus_count() == 0:
        state = 5

    if state == -2:
        delay_before_start = delay_before_start - 1
        if delay_before_start == 0:
            delay_before_start = 10
            state = 0
    if state == 0:
        # bottle.add(*next_pillow.bricks())
        pillow = bottle.add_pillow(next_pillow)
        next_pillow = Pillow.create(brick_size, [0, 0])
        # bottle.add(*next_pillow.bricks())
        state = 1
    elif state == 1:
        downkeys = pygame.key.get_pressed()
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
            if pillow and not pillow.move_down():
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
    if next_pillow:
        next_pillow.draw(next_pillow_surf)
    # --- Go ahead and update the screen with what we've drawn.
    pygame.display.flip()

    # --- Limit to 60 frames per second
    clock.tick(tick * mult)

pygame.quit()
