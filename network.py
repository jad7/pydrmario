import asyncio
import json
import logging.handlers
import threading

import pygame
import websockets
from pygame import DOUBLEBUF, RESIZABLE, SCALED
from pygame.locals import (
    KEYDOWN,
    QUIT,
)

from constants import *
from objects.bottle import Bottle
from objects.brick import init as viruses_init
from objects.draw import draw_bg
from objects.pillow import Pillow

logger = logging.getLogger("")
logger.setLevel(logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler())

pygame.init()
pygame.fastevent.init()
X = 8
Y = 17
between_bricks = 3
pygame.font.init()

bottle_offset = (50, 100)
brick_size = 20
virus_offset = 5

mute = True
next_pillow_offset = (bottle_offset[0] + X * brick_size + 20, 10)

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 500


def main():
    pygame.mixer.init()
    try:
        pygame.mixer.music.load("music_mp3/3 - Fever.mp3")
    except:
        print("ignore not found music")
    VIRUSES_COUNT = 84
    SERVER_EVENT = pygame.event.custom_type()
    sending_queue = asyncio.Queue()
    client_id = None
    game_id = None
    STOP = []

    async def send_to_ws(ws, stop):
        while not STOP:
            try:
                get = sending_queue.get()
                msg = await asyncio.wait_for(get, timeout=1)
                print(f"Sending {str(msg)}")
            except asyncio.TimeoutError:
                pass
            else:
                await ws.send(json.dumps(dict(client_id=client_id, game_id=game_id, **msg)))

    async def handle_socket(loop, stop):
        async with websockets.connect(
                'ws://localhost:5001/connect') as ws:

            loop.create_task(send_to_ws(ws, stop))
            while not stop:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=20)
                except asyncio.TimeoutError:
                    # No data in 20 seconds, check the connection.
                    try:
                        pong_waiter = await ws.ping()
                        await asyncio.wait_for(pong_waiter, timeout=10)
                    except asyncio.TimeoutError:
                        stop.append(1)
                        # TODO
                        # No response to ping in 10 seconds, disconnect.
                        break
                else:
                    pygame.event.post(pygame.event.Event(SERVER_EVENT, data=json.loads(msg)))

    def start_client(loop):
        loop.run_until_complete(handle_socket(loop, STOP))

    loop = asyncio.get_event_loop()
    thread = threading.Thread(target=start_client, args=(loop,))
    thread.start()

    # Create the screen object
    # The size is determined by the constant SCREEN_WIDTH and SCREEN_HEIGHT
    # screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), SCALED | RESIZABLE | DOUBLEBUF)
    # screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT),HWSURFACE|DOUBLEBUF|RESIZABLE)
    # fake_screen = screen.copy()
    # screen.fill(BLACK)
    draw_bg(screen, SCREEN_WIDTH, SCREEN_HEIGHT, 10)

    bottle_size = (X * (brick_size + between_bricks) - between_bricks, (Y - 1) * (brick_size + between_bricks))
    # Y-1 because position 0 is reserved, by out-of-box
    bottle_surf = screen.subsurface([bottle_offset[0], bottle_offset[1], *bottle_size])
    bottle_surf2 = screen.subsurface([bottle_offset[0] * 2 + bottle_size[0], bottle_offset[1], *bottle_size])
    bottle_surf.fill(BLACK)
    bottle_surf2.fill(BLACK)

    next_pillow_surf = screen.subsurface(
        [bottle_offset[0] + X * brick_size + 20, 10, brick_size * 2 + between_bricks, brick_size])
    pygame.draw.rect(screen, BLACK,
                     [bottle_offset[0] + X * brick_size + 20 - 10, 10 - 10, brick_size * 2 + between_bricks + 20,
                      brick_size + 20])

    # draw_bottle(screen, bottle_offset, bottle_size)
    # TODO move to bottle object
    bottle_image_raw = pygame.image.load("img/bottle.png").convert_alpha()
    bottle_image_scale = pygame.transform.scale(bottle_image_raw, (bottle_size[0] + 35, bottle_size[1] + 95))
    del bottle_image_raw
    screen.blit(bottle_image_scale, (bottle_offset[0] - 18, bottle_offset[1] - 81))
    screen.blit(bottle_image_scale, (bottle_offset[0] * 2 + bottle_size[0] - 18, bottle_offset[1] - 81))

    viruses_init()

    # tick = 10 * 3
    tick = 5 * 1

    running = True

    pause_state = None
    state = -3
    next_pillow = None
    pillow = None
    bottle: Bottle = None
    bottle2: Bottle = None
    falled = set()
    clock = pygame.time.Clock()
    delay_before_start = 10
    num = 0
    pillows = []

    def delay(actions_per_second):
        nonlocal num
        num = num + 1
        if num > (tick / actions_per_second):
            num = 0
            return True
        return False

    # pygame.key.set_repeat(200, 200)
    while running:
        mult = 0
        keys = set()
        quit_events = pygame.event.get(eventtype=QUIT)
        if quit_events:
            running = False
            STOP.append(1)

        server_events = pygame.event.get(eventtype=SERVER_EVENT)

        if server_events:
            for event in server_events:
                """
                0 - acknowledge client_id
                1 - acknowledge game_id
                2 - request generate viruses
                3 - set viruses
                4 - start_acked
                5 - changes
                6 - win
                7 - loose
                """
                data = event.data
                logger.debug(f"Received server event: {event.data}")
                cmd = data.get('cmd')
                if cmd == 0:
                    client_id = data['client_id']
                elif cmd == 1:
                    game_id = data['game_id']
                    bottle = Bottle(X, Y, brick_size, bottle_surf, capture_changes=True)
                    bottle2 = Bottle(X, Y, brick_size, bottle_surf2)
                    sending_queue.put_nowait(dict(cmd=0))
                elif cmd == 2:
                    VIRUSES_COUNT = data['virus_count']
                    state = -1
                elif cmd == 3:
                    if data['viruses']:
                        bottle.set_viruses(data['viruses'])
                        bottle2.set_viruses(data['viruses'])
                    else:
                        bottle2.set_viruses(bottle.get_viruses())

                    pillows = data['pillows']
                    sending_queue.put_nowait(dict(cmd=2))
                elif cmd == 4:
                    state = -2
                elif cmd == 5:
                    bottle2.apply_changes(data['changes'])
                elif cmd == 6 or cmd == 7:
                    state = 5
                    STOP.append(1)

        events_raw = pygame.event.get(eventtype=KEYDOWN)
        keys = {event.key: event for event in events_raw}

        if state == -3:
            pass
        if state == -1:
            if bottle:
                bottle.empty()
                bottle2.empty()

            pillow = None
            # next_pillow = Pillow.create(brick_size, [0, 0])
            bottle.populate_viruses(VIRUSES_COUNT, virus_offset)
            sending_queue.put_nowait(dict(cmd=1, viruses=bottle.get_viruses()))
            if not mute:
                pygame.mixer.music.play(-1)
            state = -3

        if bottle and bottle.virus_count() == 0:
            state = 5

        if state == -2:
            delay_before_start = delay_before_start - 1
            if delay_before_start == 0:
                delay_before_start = 10
                state = 0
        if state == 0:
            # bottle.add(*next_pillow.bricks())
            if not next_pillow:
                next_pillow = Pillow.from_data(pillows.pop(), brick_size, [0, 0]) if pillows else Pillow.create(
                    brick_size, [0, 0])

            pillow = bottle.add_pillow(next_pillow)
            state = 1 if pillow else 7
            next_pillow = Pillow.from_data(pillows.pop(), brick_size, [0, 0]) if pillows \
                else Pillow.create(brick_size, [0, 0])
            # next_pillow =
            # bottle.add(*next_pillow.bricks())

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
                mult = 15
            if pygame.K_z in keys:
                pillow.turn_uclw()
            if pygame.K_x in keys:
                pillow.turn_clw()
            if pygame.K_RETURN in keys:
                bottle.pause()
                pause_state = state
                state = 6

            if delay(2 + mult):
                if pillow and not pillow.move_down():
                    state = 2

        elif state == 2:
            if delay(4):
                if bottle.burn(pillow):
                    state = 3
                else:
                    state = 0

        elif state == 3:
            if delay(4):
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
            sending_queue.put_nowait(dict(cmd=4))
            bottle.end()
            if keys:
                if pygame.K_RETURN in keys:
                    state = -3
        elif state == 6:
            if pygame.K_RETURN in keys:
                state = pause_state
                bottle.unpause()
        elif state == 7:
            sending_queue.put_nowait(dict(cmd=7))
            bottle.end(win=False)
            if keys:
                if pygame.K_RETURN in keys:
                    state = -3

        if bottle:
            bottle.update()
            if bottle.changes.has_changes():
                to_send = bottle.pop_changes().to_dict()
                sending_queue.put_nowait(dict(cmd=3, changes=to_send))

        if bottle2:
            bottle2.update()
        if next_pillow:
            next_pillow.draw(next_pillow_surf)
        # --- Go ahead and update the screen with what we've drawn.
        pygame.display.flip()

        # --- Limit to 30 frames per second
        clock.tick(tick)

    pygame.quit()


if __name__ == "__main__":
    main()
