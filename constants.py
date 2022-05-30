from collections import namedtuple
from enum import Enum

BLACK = (0, 0, 0)

WHITE = (255, 255, 255)
BLUE = (0, 176, 240)
RED = (255, 0, 0)
YELLOW = (247, 224, 12)
GREEN = (32, 138, 18)
BOT_BLUE = (52, 235, 216)

COLOR_NAMES = {
    BLUE: "B",
    RED: "R",
    YELLOW: "Y"
}

COLOR_SHORTS = {v: k for k, v in COLOR_NAMES.items()}

COLORS = [RED, BLUE, YELLOW]


class Direction(Enum):
    LEFT = 1
    RIGHT = 2
    TOP = 3
    BOTTOM = 4


Point = namedtuple('Point', 'x y')
