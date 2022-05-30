import logging
import os
import pickle
from dataclasses import dataclass
from datetime import timedelta
from typing import Union, Callable, Optional

import gevent
from gevent import monkey

monkey.patch_all()
import redis
import random
from redis_lock import Lock as RedisLock

import json, uuid
from flask import Flask
from flask_sock import Sock
from collections.abc import Iterable
from attrdict import AttrDict

COLORS = ['R', 'B', 'Y']

import logging.handlers

logger = logging.getLogger("")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# handler.setFormatter(formatter)
logging.getLogger().addHandler(logging.StreamHandler())

REDIS_URL = os.environ.get('REDIS_URL', "redis://localhost:6379")
REDIS_TO_PLAY = 'ready_to_play'
REDIS_MSGS = 'messages'
GAMES_PREFIX = 'games:v1:'

app = Flask(__name__)
app.debug = 'DEBUG' in os.environ

sockets = Sock(app)
redis = redis.from_url(REDIS_URL)

VIRUS_COUNT = 20


def get_game(game_id) -> Optional["Game"]:
    data = redis.get(GAMES_PREFIX + game_id)
    if data:
        return pickle.loads(data)
    else:
        return None


def update_game(game_id, game: "Game"):
    redis.set(GAMES_PREFIX + game_id, pickle.dumps(game), ex=timedelta(hours=1))


class ServerBackend(object):
    """Interface for registering and updating WebSocket clients."""

    def __init__(self):
        self.clients = dict()
        self.pubsub = redis.pubsub()
        self.pubsub.subscribe(REDIS_MSGS)

    def __iter_data(self):
        for message in self.pubsub.listen():
            data = message.get('data')
            if message['type'] == 'message':
                app.logger.info(u'Sending message: {}'.format(data))
                yield AttrDict(json.loads(data))

    def register_client(self, wsocket) -> "Client":
        client = Client(wsocket)
        self.clients[client.id] = client
        client.acknowledge_id()
        logger.debug(f"Registered new client: {client.id}")
        return client

    def add_to_waiters(self, waiter: "Client"):
        redis.lpush(REDIS_TO_PLAY, json.dumps(waiter.id))

    def run(self):
        """Listens for new messages in Redis, and sends them to clients."""
        for data in self.__iter_data():
            if data.client_id in self.clients:
                gevent.spawn(getattr(self.clients[data.client_id], data.method), **data.obj)

    def find_partner(self):
        id = redis.lpop(REDIS_TO_PLAY)
        return json.loads(id) if id else None

    def start(self):
        """Maintains Redis subscription in the background."""
        gevent.spawn(self.run)

    def start_game(self, client1: "Client", client2_id: str):
        game_id = str(uuid.uuid4())
        game = Game(game_id, client1_id=client1.id, client2_id=client2_id)
        update_game(game_id, game)
        self.exec_method([client1.id, client2_id], Client.ack_gameid, game=game)

    def exec_method(self, client_ids: Union[str, Iterable], method: Callable, **kwargs):
        if isinstance(client_ids, str):
            client_ids = [client_ids]
        for client_id in client_ids:
            if client_id in self.clients:
                gevent.spawn(getattr(self.clients[client_id], method.__name__), **kwargs)
            else:
                redis.publish(REDIS_MSGS, json.dumps(dict(client_id=client_id, method=method.__name__, obj=kwargs)))

    def delete_client(self, id):
        del self.clients[id]


server = ServerBackend()
server.start()


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

    def acknowledge_id(self):
        self.send(cmd=0, client_id=self.id)

    def ack_gameid(self, game: "Game"):
        self.game = game
        self.send(cmd=1, game_id=game.game_id)

    def generate_viruses(self, virus_count):
        self.send(cmd=2, virus_count=virus_count)

    def start_ack(self):
        self.send(cmd=4)

    def set_viruses(self, viruses, pillows):
        self.send(cmd=3, viruses=viruses, pillows=pillows)

    def send_changes(self, changes):
        self.send(cmd=5, changes=changes)

    def win(self):
        self.send(cmd=6)
        self.socket.close()
        server.delete_client(self.id)

    def loose(self):
        self.send(cmd=7)
        self.socket.close()
        server.delete_client(self.id)

    def get_partner_id(self):
        if self.game:
            clients = self.game.clients()
            clients.remove(self.id)
            return clients[0]

    def send(self, cmd: int, **data):
        """Send given data to the registered client.
        Automatically discards invalid connections."""
        try:
            self.socket.send(json.dumps(dict(cmd=cmd, **data)))
        except Exception as e:
            logging.error("Communication error", e)
            # TODO close connection
            # self.clients.remove(client)

    def handle_message(self, msg):
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
        4-done
        """
        msg_obj = AttrDict(json.loads(msg))
        if game_id := msg_obj.game_id:
            logging.debug(f"GameId: {game_id}, ClientId: {self.id}, msg: {str(msg)}")
            if msg_obj.cmd == 0:
                with RedisLock(redis, "game_lock:" + game_id, id=self.id):
                    game: Game = get_game(game_id)
                    game.ack_ready(msg_obj.client_id, 1)
                    update_game(game_id, game)
                if game and game.is_both_acc(1):
                    server.exec_method(game.client1_id, Client.generate_viruses, virus_count=VIRUS_COUNT)
            elif msg_obj.cmd == 1:
                pillows = generate_pillows()
                self.set_viruses(viruses=None, pillows=pillows)
                server.exec_method(self.get_partner_id(), Client.set_viruses, viruses=msg_obj.viruses, pillows=pillows)

            elif msg_obj.cmd == 2:
                with RedisLock(redis, "game_lock:" + game_id, id=self.id):
                    game: Game = get_game(game_id)
                    game.ack_ready(msg_obj.client_id, 2)
                    update_game(game_id, game)
                if game and game.is_both_acc(2):
                    server.exec_method(self.game.clients(), Client.start_ack)
            elif msg_obj.cmd == 3:
                server.exec_method(self.get_partner_id(), Client.send_changes, changes=msg_obj.changes)
            elif msg_obj.cmd == 4:
                with RedisLock(redis, "game_lock:" + game_id, id=self.id):
                    game: Game = get_game(game_id)
                    if game.win is None:
                        game.win = self.id
                    update_game(game_id, game)
                if game.win == self.id:
                    self.win()
                    server.exec_method(self.get_partner_id(), Client.loose)
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


@app.route('/')
def hello():
    return "Hi!"


@sockets.route('/connect')
def connect(ws, *args, **kwargs):
    logging.info("New connection" + str(ws))
    """Connect client"""
    client: Client = server.register_client(ws)
    partner_id = server.find_partner()
    if partner_id:
        logger.debug(f"For client {client.id} found partner {partner_id}")
        server.start_game(client, partner_id)
    else:
        server.add_to_waiters(client)

    while ws.connected:
        # Sleep to prevent *constant* context-switches.
        gevent.sleep(0.1)
        message = ws.receive()
        try:
            if not client.handle_message(message):
                ws.close()
                return
        except Exception as e:
            logging.error("handling error", e)


if __name__ == "__main__":
    # from gevent import pywsgi
    # from geventwebsocket.handler import WebSocketHandler

    # from gevent.pywsgi import WSGIServer
    # server = WSGIServer(('127.0.0.1', 5001), app)
    # server.serve_forever()
    app.run('127.0.0.1', 5001)
