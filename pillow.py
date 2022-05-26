import random

from brick import Brick
from constants import *


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
