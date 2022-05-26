from collections import namedtuple
from enum import Enum

BLACK = (0, 0, 0)

WHITE = (255, 255, 255)
BLUE = (0, 176, 240)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

COLOR_NAMES = {
    BLUE: "B",
    RED: "R",
    YELLOW: "Y"
}

COLORS = [RED, BLUE, YELLOW]


class Direction(Enum):
    LEFT = 1
    RIGHT = 2
    TOP = 3
    BOTTOM = 4


Point = namedtuple('Point', 'x y')
