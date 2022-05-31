import asyncio
import json
import logging
import logging.handlers
import os
import pickle
import random
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import timedelta
from typing import Union, Callable, Optional

import aioredis
import async_timeout
import websockets
from aioredis import Redis
from aioredis_lock import RedisLock
from attrdict import AttrDict

logger = logging.getLogger("")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# handler.setFormatter(formatter)
logging.getLogger().addHandler(logging.StreamHandler())

COLORS = ['R', 'B', 'Y']

REDIS_URL = os.environ.get('REDIS_URL', "redis://localhost:6379")
REDIS_TO_PLAY = 'ready_to_play'
REDIS_MSGS = 'messages'
GAMES_PREFIX = 'games:v1:'

redis: Optional[Redis] = None
server: Optional["Server"] = None

VIRUS_COUNT = 10


async def get_game(game_id) -> Optional["Game"]:
    data = await redis.get(GAMES_PREFIX + game_id)
    if data:
        return pickle.loads(data)
    else:
        return None


async def update_game(game_id, game: "Game"):
    await redis.set(GAMES_PREFIX + game_id, pickle.dumps(game), expire=timedelta(hours=1).seconds)


class ServerBackend(object):
    """Interface for registering and updating WebSocket clients."""

    def __init__(self):
        self.clients = dict()

    async def __iter_data(self):
        subscribe = await redis.subscribe(REDIS_MSGS)
        while await subscribe[0].wait_message():
            try:
                async with async_timeout.timeout(1):
                    message = await subscribe.get(encoding='utf-8')
                    if message:
                        data = message.get('data')
                        if message['type'] == 'message':
                            logger.info(u'Sending message: {}'.format(data))
                            yield AttrDict(json.loads(data))
                        await asyncio.sleep(0.01)
            except asyncio.TimeoutError:
                pass

    async def register_client(self, wsocket) -> "Client":
        client = Client(wsocket)
        self.clients[client.id] = client
        await client.acknowledge_id()
        logger.debug(f"Registered new client: {client.id}")
        return client

    async def add_to_waiters(self, waiter: "Client"):
        await redis.lpush(REDIS_TO_PLAY, json.dumps(waiter.id))

    async def handle_pubsub(self):

        """Listens for new messages in Redis, and sends them to clients."""
        task = None
        async for data in self.__iter_data():
            if data.client_id in self.clients:
                task = asyncio.create_task(getattr(self.clients[data.client_id], data.method)(**data.obj))

    async def find_partner(self):
        id = await redis.lpop(REDIS_TO_PLAY)
        return json.loads(id) if id else None

    async def start_game(self, client1: "Client", client2_id: str):
        game_id = str(uuid.uuid4())
        game = Game(game_id, client1_id=client1.id, client2_id=client2_id)
        await update_game(game_id, game)
        await self.exec_method([client1.id, client2_id], Client.ack_gameid, game_id=game_id)

    async def exec_method(self, client_ids: Union[str, Iterable], method: Callable, **kwargs):
        task = None
        if isinstance(client_ids, str):
            client_ids = [client_ids]
        for client_id in client_ids:
            if client_id in self.clients:
                task = asyncio.create_task(getattr(self.clients[client_id], method.__name__)(**kwargs))
                # await getattr(self.clients[client_id], method.__name__)(**kwargs)
            else:
                redis.publish(REDIS_MSGS, json.dumps(dict(client_id=client_id, method=method.__name__, obj=kwargs)))

    def delete_client(self, id):
        del self.clients[id]


def generate_pillows():
    return [(random.choice(COLORS), random.choice(COLORS)) for _ in range(1000)]


class Client:
    """
    Interface
    0 - acknowledge client_id
    1 - acknowledge game_id
    2 - request generate viruses
    3 - set viruses
    4 - start_acked
    5 - changes
    6 - win
    7 - loose
    """

    def __init__(self, wsocket):
        self.id = str(uuid.uuid4())
        self.socket = wsocket
        self.game = None
        self.num = 0

    async def acknowledge_id(self):
        await self.send(cmd=0, client_id=self.id)

    async def ack_gameid(self, game_id):
        self.game = await get_game(game_id)
        self.num = (1 if self.game.client1_id == self.id else 2)
        await self.send(cmd=1, game_id=game_id)

    async def generate_viruses(self, virus_count):
        await self.send(cmd=2, virus_count=virus_count)

    async def start_ack(self):
        await self.send(cmd=4)

    async def set_viruses(self, viruses, pillows):
        await self.send(cmd=3, viruses=viruses, pillows=pillows)

    async def send_changes(self, changes):
        await self.send(cmd=5, changes=changes)

    async def win(self):
        await self.send(cmd=6)
        self.socket.close()
        server.delete_client(self.id)

    async def loose(self):
        await self.send(cmd=7)
        await self.socket.close()
        server.delete_client(self.id)

    def get_partner_id(self):
        if self.game:
            clients = self.game.clients()
            clients.remove(self.id)
            return clients[0]

    async def send(self, cmd: int, **data):
        """Send given data to the registered client.
        Automatically discards invalid connections."""
        try:
            logging.debug(f"Sending msg to client_{self.num} {self.id} with cmd={cmd}")
            await self.socket.send(json.dumps(dict(cmd=cmd, **data)))
        except Exception as e:
            logging.error("Communication error")
            # TODO close connection
            # self.clients.remove(client)

    async def handle_message(self, msg):
        """
        msg = {
        cmd : int
        game_id: str
        client_id: str
        ...
        }
        0-ack ready
        1-viruses
        2-all start ready
        3-send changes
        4-done win
        5-done loose
        """
        msg_obj = AttrDict(json.loads(msg))
        if game_id := msg_obj.game_id:
            logging.debug(f"GameId: {game_id}, ClientId: {self.id}, msg: {str(msg)}")
            if msg_obj.cmd == 0:
                async with RedisLock(redis, "game_lock:" + game_id):
                    game: Game = await get_game(game_id)
                    game.ack_ready(msg_obj.client_id, 1)
                    await update_game(game_id, game)
                if game and game.is_both_acc(1):
                    await server.exec_method(game.client1_id, Client.generate_viruses, virus_count=VIRUS_COUNT)
            elif msg_obj.cmd == 1:
                pillows = generate_pillows()
                await self.set_viruses(viruses=None, pillows=pillows)
                await server.exec_method(self.get_partner_id(), Client.set_viruses, viruses=msg_obj.viruses,
                                         pillows=pillows)

            elif msg_obj.cmd == 2:
                async with RedisLock(redis, "game_lock:" + game_id):
                    game: Game = await get_game(game_id)
                    game.ack_ready(msg_obj.client_id, 2)
                    await update_game(game_id, game)
                if game and game.is_both_acc(2):
                    await server.exec_method(self.game.clients(), Client.start_ack)
            elif msg_obj.cmd == 3:
                await server.exec_method(self.get_partner_id(), Client.send_changes, changes=msg_obj.changes)
            elif msg_obj.cmd == 4:
                async with RedisLock(redis, "game_lock:" + game_id):
                    game: Game = await get_game(game_id)
                    if game.win is None:
                        game.win = self.id
                    await update_game(game_id, game)
                if game.win == self.id:
                    await self.win()
                    await server.exec_method(self.get_partner_id(), Client.loose)
            return True
        elif msg_obj.cmd == 5:
            with RedisLock(redis, "game_lock:" + game_id, id=self.id):
                game: Game = await get_game(game_id)
                if game.win is None:
                    game.win = self.get_partner_id()
                await update_game(game_id, game)
            if game.win == self.get_partner_id():
                await self.loose()
                await server.exec_method(self.get_partner_id(), Client.win)
        return True


@dataclass
class GameConfig:
    ack: int = 0
    viruses_count: int = None


@dataclass
class Game:
    game_id: str
    client1_id: str
    client2_id: str
    client1_config: "GameConfig" = GameConfig()
    client2_config: "GameConfig" = GameConfig()
    win: str = None

    def ack_ready(self, client_id, val=1):
        if client_id not in (self.client1_id, self.client2_id):
            logging.warning(f"Illegal state client {client_id} connected to game {self.game_id} "
                            f"with {(self.client1_id, self.client2_id)}. Where he's not a part of.")
            return False
        cfg = self.client1_config if self.client1_id == client_id else self.client2_config
        cfg.ack = val
        return True

    def is_both_acc(self, val):
        return self.client2_config.ack == val and self.client2_config.ack == val

    def clients(self):
        return [self.client1_id, self.client2_id]


async def reactor(ws):
    logging.info("New connection" + str(ws))
    """Connect client"""
    client: Client = await server.register_client(ws)
    partner_id = await server.find_partner()
    if partner_id:
        logger.debug(f"For client {client.id} found partner {partner_id}")
        await server.start_game(client, partner_id)
    else:
        await server.add_to_waiters(client)
    async for message in ws:
        try:
            if not await client.handle_message(message):
                ws.close()
                return
        except websockets.ConnectionClosedOK:
            break
        except Exception as e:
            logging.error("handling error", e)


if __name__ == "__main__":
    # from gevent import pywsgi
    # from geventwebsocket.handler import WebSocketHandler

    # from gevent.pywsgi import WSGIServer
    # server = WSGIServer(('127.0.0.1', 5001), app)
    # server.serve_forever()
    async def main():
        global redis, server
        redis = await aioredis.create_redis_pool(REDIS_URL)
        server = ServerBackend()
        async with websockets.serve(reactor, "localhost", 5001):
            await server.handle_pubsub()
            await asyncio.Future()  # run forever


    asyncio.run(main())
