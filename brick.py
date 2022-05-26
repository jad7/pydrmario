import functools
import itertools
import random
from builtins import set
from collections import namedtuple
from enum import Enum
from typing import Any, Tuple, List, Set, Optional

import pygame

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

viruses = {}
pillows = {}


@functools.lru_cache()
def transform_image(image, scale):
    return pygame.transform.scale(image, scale)


@functools.lru_cache()
def get_pillow(color, direction: Optional[Direction], size):
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


def init():
    global viruses
    viruses = {
        BLUE: pygame.image.load("virus_blue.png").convert(),
        RED: pygame.image.load("virus_red.png").convert(),
        YELLOW: pygame.image.load("virus_yel.png").convert()
    }

    for img in viruses.values():
        img.set_colorkey((0, 0, 0))


class Bottle(pygame.sprite.Group):

    def __init__(self, X, Y, brick_size, offset, *sprites):
        super().__init__(*sprites)
        self.offset = offset
        self.X = X
        self.Y = Y
        self.brick_size = brick_size
        self.bottle = [[None for x in range(Y)] for y in range(X)]
        self.positions = dict()
        self.viruses = 0
        self.pause_text = Text("Pause!", 30, BLUE, int(self.X * self.brick_size / 2), int(self.Y * self.brick_size / 2))

    def populate_viruses(self, count, y_offset):
        free = [Point(x, y + y_offset) for x in range(self.X) for y in range(self.Y - y_offset)]
        self.viruses = 0
        while self.viruses < count:
            random.shuffle(free)
            new_bricks = []
            while self.viruses < count and free:
                point = free.pop()
                b = Brick(COLORS[int(random.random() * len(COLORS))], self.brick_size, self.brick_size, self.offset,
                          virus=True, position=point)
                new_bricks.append(b)
                self.viruses = self.viruses + 1
                self[point] = b
                self.add(b)

            burned = self.burn_bricks(new_bricks, 3)
            # self.viruses = self.viruses - len(burned)
            free = list(burned) + free

    def add_pillow(self, pillow: "Pillow"):
        pillow.update_offset(self.offset)
        pillow.add_to_bottle(self, (2, 1))
        # self.add(*pillow.bricks())
        return pillow

    def __getitem__(self, item):
        if isinstance(item, Point):
            return self.bottle[item.x][item.y]
        if isinstance(item, Tuple):
            return self.bottle[item[0]][item[1]]
        return self.bottle[item]

    def __setitem__(self, key, value):
        if isinstance(key, Tuple):
            self.bottle[key[0]][key[1]] = value
            return
        self.bottle[key] = value

    def burn(self, *pillows: 'Pillow'):
        # print("start burn")
        bricks = filter(lambda z: z, list(itertools.chain(*[p.bricks() for p in pillows])))
        return self.burn_bricks(bricks)

    def burn_bricks(self, bricks, max_count=4):
        t: Set[Point] = set()
        for b in bricks:
            t.update(self._burn(b, max_count))
        for point in t:
            br = self[point]
            self[point] = None
            br.kill()
            if br.is_virus():
                self.viruses = self.viruses - 1
        # print("end burn")
        # if sum(1 for Ys in self.bottle for x in Ys if x and x.is_virus()) != self.viruses:
        #    print("Here error")

        return t

    def _burn(self, br: 'Brick', max_count=4) -> List[Point]:
        if not br:
            return []
        i = Point(br.x, br.y)
        to_del = []
        # move left
        hor_same = []
        while i.x > 0 and (b := self[i.x - 1][i.y]) and b.color == br.color:
            i = Point(i.x - 1, i.y)
        # move right
        hor_same.append(i)
        while i.x + 1 < self.X and (b := self[i.x + 1][i.y]) and b.color == br.color:
            i = Point(i.x + 1, i.y)
            hor_same.append(i)

        if len(hor_same) >= max_count:
            to_del.extend(hor_same)

        i = Point(br.x, br.y)
        # move up
        ver_same = []
        while i.y > 0 and (b := self[i.x, i.y - 1]) and b.color == br.color:
            i = Point(i.x, i.y - 1)
        # move down
        ver_same.append(i)
        while i.y + 1 < self.Y and (b := self[i.x, i.y + 1]) and b.color == br.color:
            i = Point(i.x, i.y + 1)
            ver_same.append(i)

        if len(ver_same) >= max_count:
            to_del.extend(ver_same)

        return to_del

    def virus_count(self) -> int:
        return self.viruses

    def fallout(self) -> List[Point]:
        print("start fallout")
        visited = set()
        step_not_made = []
        falled = []
        for y in range(self.Y - 2, 0, -1):
            for x in range(self.X):
                if self[x, y] and not self[x, y].is_virus():
                    pillow = self[x, y].pillow
                    if pillow not in visited:
                        visited.add(pillow)
                        if pillow.move_down():
                            falled.append(pillow)
                        else:
                            step_not_made.append(pillow)
        if falled:
            for pillow in step_not_made:
                if pillow.move_down():
                    falled.append(pillow)
        print("end fallout")
        return falled

    def end(self):
        self.empty()
        self.viruses = 0
        # my_font = pygame.font.SysFont('Comic Sans MS', 30)
        # text_surface = my_font.render('Done!', False, BLUE)
        self.add(Text("Done!", 30, BLUE, int(self.X * self.brick_size / 2), int(self.Y * self.brick_size / 2)))
        # self.image = pygame.Surface([width, height])
        # self.image.fill(color)
        # self.image.set_colorkey(BLACK)

    def pause(self):
        self.add(self.pause_text)

    def unpause(self):
        self.pause_text.kill()


class Text(pygame.sprite.Sprite):
    def __init__(self, text, size, color, width, height):
        # Call the parent class (Sprite) constructor
        pygame.sprite.Sprite.__init__(self)

        self.font = pygame.font.SysFont("Comic Sans MS", size)
        self.textSurf = self.font.render(text, 1, color)
        self.image = pygame.Surface((width, height))
        W = self.textSurf.get_width()
        H = self.textSurf.get_height()
        self.image.blit(self.textSurf, [width / 2 - W / 2, height / 2 - H / 2])
        self.rect = self.image.get_rect()


class Pillow:
    def __init__(self, brick1, brick2):
        self.bottle = None
        self.brick1: Brick = brick1
        brick1.pillow = self
        self.brick2: Brick = brick2
        brick2.pillow = self

        '''
        0 - (1,2)
        
              (1)
        1 -   (2)
        
        2 - (2,1)
        
              (2)
        3 -   (1)
        '''
        self.position = 0
        self.update_position()

    def add_to_bottle(self, bottle, position):
        self.bottle = bottle
        bottle.bottle[position[0]][position[1]] = self.brick1
        bottle.bottle[position[0] + 1][position[1]] = self.brick2
        self.brick1.position = [position[0], position[1]]
        self.brick2.position = [position[0] + 1, position[1]]

    def move_down(self) -> bool:
        b = self.bottle
        br1 = self.brick1
        br2 = self.brick2

        if not br1 or not br2:
            br = br1 or br2
            if br.can_down(b):
                br.move_down(b)
                return True

        elif self.is_horz():
            if br1.can_down(b) and br2.can_down(b):
                br1.move_down(b)
                br2.move_down(b)
                return True
        else:
            upper, lower = (br1, br2) if self.position == 1 else (br2, br1)
            if lower.can_down(b):
                lower.move_down(b)
                upper.move_down(b)
                return True

        return False

    def can_down(self):
        b = self.bottle
        br1 = self.brick1
        br2 = self.brick2

        if not br1 or not br2:
            br = br1 or br2
            return br.can_down(b)

        if self.is_horz():
            if br1.can_down(b) and br2.can_down(b):
                return True
        else:
            upper, lower = (br1, br2) if self.position == 1 else (br2, br1)
            if lower.can_down(b):
                return True

        return False

    def move_left(self):
        b = self.bottle
        br1 = self.brick1
        br2 = self.brick2

        if self.is_horz():
            left, right = (br1, br2) if self.position == 0 else (br2, br1)
            if left.can_left(b):
                left.move_left(b)
                right.move_left(b)
        elif br1.can_left(b) and br2.can_left(b):
            br1.move_left(b)
            br2.move_left(b)

    def move_right(self):
        b = self.bottle
        br1 = self.brick1
        br2 = self.brick2

        if self.is_horz():
            left, right = (br1, br2) if self.position == 0 else (br2, br1)
            if right.can_right(b):
                right.move_right(b)
                left.move_right(b)
        elif br1.can_right(b) and br2.can_right(b):
            br1.move_right(b)
            br2.move_right(b)

    '''
    z -> 
                (2)_     
        (1,2) ->(1)_ 
    
    x->
                (1)_     
        (1,2) ->(2)_   
        
        (1)_
        (2)_  -> (2, 1)    
    
            0 - (1,2)

                  (1)
            1 -   (2)

            2 - (2,1)

                  (2)
            3 -   (1)
            '''

    def turn_clw(self):
        b = self.bottle
        br1 = self.brick1
        br2 = self.brick2

        if self.is_horz():
            left, right = (br1, br2) if self.position == 0 else (br2, br1)
            if left.y == 0 or b[left.x, left.y - 1] is None:
                left.move_up(b)
                right.move_left(b)
                self.position = self.position + 1
                self.update_position()
        else:
            upper, lower = (br1, br2) if self.position == 1 else (br2, br1)
            if lower.can_right(b):
                upper.move_right_down(b)
                self.position = (self.position + 1) % 4
                self.update_position()
            elif lower.can_left(b):
                lower.move_left(b)
                upper.move_down(b)
                self.position = (self.position + 1) % 4
                self.update_position()

        # if self.position ==

    def is_horz(self):
        return self.position in [0, 2]

    def __eq__(self, other):
        return isinstance(other, Pillow) and (self.brick1, self.brick2) == (other.brick1, other.brick2)

    def __hash__(self):
        return hash((self.brick1, self.brick2))

    def turn_uclw(self):
        b = self.bottle
        br1 = self.brick1
        br2 = self.brick2

        if self.is_horz():
            left, right = (br1, br2) if self.position == 0 else (br2, br1)
            if left.y == 0 or b[left.x][left.y - 1] is None:
                right.move_left_up(b)
                self.position = (self.position - 1) % 4
                self.update_position()
        else:
            upper, lower = (br1, br2) if self.position == 1 else (br2, br1)
            if lower.can_right(b):
                lower.move_right(b)
                upper.move_down(b)
                self.position = self.position - 1
                self.update_position()
            elif lower.can_left(b):
                upper.move_left_down(b)
                self.position = self.position - 1
                self.update_position()

        return None

    def bricks(self):
        return [self.brick1, self.brick2]

    def kill_brick(self, b: 'Brick'):
        if self.brick1 is b:
            self.brick1 = None
        else:
            self.brick2 = None
        self.update_position()

    def update_offset(self, offset):
        if self.brick1:
            self.brick1.offset = offset
        if self.brick2:
            self.brick2.offset = offset

    def update_position(self):
        br1 = self.brick1
        br2 = self.brick2
        if not br1 and not br2:
            return
        if not br1 or not br2:
            br = br1 or br2
            br.set_direction(None)
        elif self.is_horz():
            left, right = (br1, br2) if self.position == 0 else (br2, br1)
            left.set_direction(Direction.LEFT)
            right.set_direction(Direction.RIGHT)
        else:
            upper, lower = (br1, br2) if self.position == 1 else (br2, br1)
            upper.set_direction(Direction.TOP)
            lower.set_direction(Direction.BOTTOM)

    @classmethod
    def create(cls, brick_size, offset):
        return Pillow(
            Brick(COLORS[int(random.random() * len(COLORS))], brick_size, brick_size, offset, position=(0, 0)),
            Brick(COLORS[int(random.random() * len(COLORS))], brick_size, brick_size, offset, position=(1, 0))
        )


class Brick(pygame.sprite.Sprite):
    # This class represents a brick. It derives from the "Sprite" class in Pygame.

    def __init__(self, color, width, height, offset, **kwargs):
        # Call the parent class (Sprite) constructor
        super().__init__()

        # Pass in the color of the brick, and its x and y position, width and height.
        # Set the background color and set it to be transparent
        self.color = color
        self.brick_size = width

        # self.image = pygame.Surface([width, height])

        self.position: List[int, int] = list(kwargs.get("position", [None, None]))
        self.pillow = kwargs.get("pillow")
        self.virus = kwargs.get("virus", False)
        self.offset = offset

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

    def move_left(self, b: Bottle):
        b[self.x - 1][self.y] = self
        b[self.x, self.y] = None
        self.x = self.x - 1

    def move_right(self, b: Bottle):
        b[self.x + 1][self.y] = self
        b[self.x][self.y] = None
        self.x = self.x + 1

    def move_up(self, b: Bottle):
        b[self.x][self.y - 1] = self
        b[self.x][self.y] = None
        self.y = self.y - 1

    def move_left_down(self, b: Bottle):
        b[self.x - 1][self.y + 1] = self
        b[self.x][self.y] = None
        self.x = self.x - 1
        self.y = self.y + 1

    def move_right_down(self, b: Bottle):
        b[self.x + 1][self.y + 1] = self
        b[self.x][self.y] = None
        self.x = self.x + 1
        self.y = self.y + 1

    def move_left_up(self, b: Bottle):
        b[self.x - 1][self.y - 1] = self
        b[self.x][self.y] = None
        self.x = self.x - 1
        self.y = self.y - 1

    def can_left(self, b: Bottle):
        return self.x > 0 and b[self.x - 1][self.y] is None

    def can_right(self, b: Bottle):
        return self.x + 1 < b.X and b[self.x + 1][self.y] is None

    def can_down(self, b: Bottle):
        return self.y + 1 < b.Y and b[self.x, self.y + 1] is None

    def move_down(self, b: Bottle):
        b[self.x, self.y + 1] = self
        b[self.x, self.y] = None
        self.y = self.y + 1

    def set_direction(self, direction):
        self.image = get_pillow(self.color, direction, self.image.get_rect().height).copy()
        self.rect = self.image.get_rect()

    def update(self, *args: Any, **kwargs: Any) -> None:
        # if self.position == [None, None]:
        #    self.kill()
        # super(Brick, self).update(self, *args, **kwargs)
        #    return

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
