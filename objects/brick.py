import functools
from typing import Any, List, Optional

import pygame

from constants import *


@functools.lru_cache()
def transform_image(image, scale):
    return pygame.transform.scale(image, scale)


@functools.lru_cache()
def get_brick_img(color, direction: Optional[Direction], size):
    radius = max(1, size // 4)
    image = pygame.Surface([size, size])
    # image.fill(color)
    image.set_colorkey(BLACK)
    # border_top_left_radius=-1, border_top_right_radius=-1, border_bottom_left_radius=-1, border_bottom_right_radius=-1
    rad_names = {
        "border_top_left_radius": -1,
        "border_top_right_radius": -1,
        "border_bottom_right_radius": -1,
        "border_bottom_left_radius": -1
    }
    res = {}
    for k, v in rad_names.items():
        if not direction or direction.name.lower() in k:
            res[k] = radius
        else:
            res[k] = v
    pygame.draw.rect(image, color, [0, 0, size, size], width=0, **res)
    width = max(1, size // 7)
    if direction == Direction.TOP or direction == None:
        pygame.draw.line(image, WHITE, (radius, radius), (radius, size - radius), width=width)
        pygame.draw.line(image, WHITE, (radius, radius), (radius + width, radius - width), width=width)
    elif direction == Direction.LEFT:
        pygame.draw.line(image, WHITE, (radius, radius), (size - radius, radius), width=width)
        pygame.draw.line(image, WHITE, (radius, radius), (radius - width, radius + width), width=width)
    elif direction == Direction.RIGHT:
        pygame.draw.line(image, WHITE, (0, radius), (size - radius, radius), width=width)
    elif direction == Direction.BOTTOM:
        pygame.draw.line(image, WHITE, (radius, 0), (radius, size - radius), width=width)
    return image


viruses = {}


def init():
    global viruses
    viruses = {
        BLUE: pygame.image.load("img/virus_blue.png").convert(),
        RED: pygame.image.load("img/virus_red.png").convert(),
        YELLOW: pygame.image.load("img/virus_yel.png").convert()
    }

    for img in viruses.values():
        img.set_colorkey((0, 0, 0))


ID = 0

class Brick(pygame.sprite.Sprite):

    # This class represents a brick. It derives from the "Sprite" class in Pygame.

    def __init__(self, color, width, height, offset, **kwargs):
        # Call the parent class (Sprite) constructor
        super().__init__()

        # Pass in the color of the brick, and its x and y position, width and height.
        # Set the background color and set it to be transparent
        global ID
        arg_id = kwargs.get("id")
        if arg_id is not None:
            self.id = arg_id
            ID = max(ID, arg_id) + 1
        else:
            self.id = ID
            ID = ID + 1
        self.color = color
        self.brick_size = width

        # self.image = pygame.Surface([width, height])

        self.position: List[int, int] = list(kwargs.get("position", [None, None]))
        self.pillow = kwargs.get("pillow")
        self.virus = kwargs.get("virus", False)
        self.offset = offset
        self.direction = kwargs.get("direction", Direction.NONE)

        # Draw the brick (a rectangle!)
        #
        if self.virus:
            # self.rect = pygame.Rect(0, 0, width, height)
            self.image = transform_image(viruses[color], (width, height))
            # pygame.draw.rect(self.image, BLACK, [2, 2, 3, 3])
        else:
            self.image = pygame.Surface([width, height])
            self.image.fill(color)
            self.image.set_colorkey(BLACK)
            pygame.draw.rect(self.image, color, [0, 0, width, height])

        # Fetch the rectangle object that has the dimensions of the image.
        self.rect = self.image.get_rect()

    def is_virus(self):
        return self.virus

    def move_left(self, b: "Bottle"):
        b[self.x - 1][self.y] = self
        b[self.x, self.y] = None
        self.x = self.x - 1

    def move_right(self, b: "Bottle"):
        b[self.x + 1][self.y] = self
        b[self.x][self.y] = None
        self.x = self.x + 1

    def move_up(self, b: "Bottle"):
        b[self.x][self.y - 1] = self
        b[self.x][self.y] = None
        self.y = self.y - 1

    def move_left_down(self, b: "Bottle"):
        b[self.x - 1][self.y + 1] = self
        b[self.x][self.y] = None
        self.x = self.x - 1
        self.y = self.y + 1

    def move_right_down(self, b: "Bottle"):
        b[self.x + 1][self.y + 1] = self
        b[self.x][self.y] = None
        self.x = self.x + 1
        self.y = self.y + 1

    def move_left_up(self, b: "Bottle"):
        b[self.x - 1][self.y - 1] = self
        b[self.x][self.y] = None
        self.x = self.x - 1
        self.y = self.y - 1

    def can_left(self, b: "Bottle"):
        return self.x > 0 and b[self.x - 1][self.y] is None

    def can_right(self, b: "Bottle"):
        return self.x + 1 < b.X and b[self.x + 1][self.y] is None

    def can_down(self, b: "Bottle"):
        return self.y + 1 < b.Y and b[self.x, self.y + 1] is None

    def move_down(self, b: "Bottle"):
        b[self.x, self.y + 1] = self
        b[self.x, self.y] = None
        self.y = self.y + 1

    def set_direction(self, direction):
        if self.direction != direction:
            self.direction = direction
            direction = None if direction == Direction.NONE else direction
            self.image = get_brick_img(self.color, direction, self.image.get_rect().height).copy()
            self.rect = self.image.get_rect()

    def update(self, *args: Any, **kwargs: Any) -> None:
        self.rect.x = self.x * (self.brick_size + 3) + self.offset[0]
        self.rect.y = self.y * (self.brick_size + 3) + self.offset[1]

    def __getattribute__(self, item):
        if item == "row" or item == "y":
            return self.position[1]
        if item == "col" or item == "x":
            return self.position[0]
        return super().__getattribute__(item)

    def __setattr__(self, key, value):
        if key == "row" or key == "y":
            self.position[1] = value
            return
        if key == "col" or key == "x":
            self.position[0] = value
            return
        return super().__setattr__(key, value)

    def tpl(self):
        return (self.x, self.y, self.color)

    def __str__(self):
        return str(self._tpl())

    def __repr__(self):
        return str((COLOR_NAMES[self.color], "V" if self.virus else "P", self.position))

    def kill(self) -> None:
        if self.pillow:
            self.pillow.kill_brick(self)
        super().kill()
