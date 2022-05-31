import itertools
import random
from builtins import set
from collections.abc import Iterable
from typing import Tuple, List, Set, Any

import pygame

from constants import *
from .brick import Brick
from .changes import Changes, CBrick


class Bottle(pygame.sprite.Group):
    def __init__(self, X, Y, brick_size, bottle_surface, capture_changes=False, *sprites):
        super().__init__(*sprites)
        self.offset = [0, -brick_size]
        self.X = X
        self.Y = Y
        self.brick_size = brick_size
        self.bottle = [[None for x in range(Y)] for y in range(X)]
        self.positions = dict()
        self.viruses = 0
        self.surf = bottle_surface
        self.pause_text = Text("Pause!", 30, BLUE, int(self.X * self.brick_size / 2), int(self.Y * self.brick_size / 2))
        self.capture_changes = capture_changes
        self.changes = Changes()
        self.id_index = dict()

    def update(self, *args: Any, **kwargs: Any) -> None:
        super().update()
        self.surf.fill(BLACK)
        self.draw(self.surf)

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
                self.id_index[b.id] = b
                self.viruses = self.viruses + 1
                self[point] = b
                self.add(b)

            burned = self.burn_bricks(new_bricks, 3)
            free = list(burned) + free

    def add_pillow(self, pillow: "Pillow"):
        pillow.update_offset(self.offset)
        if pillow.add_to_bottle(self, (3, 1)):
            for brick in pillow.bricks():
                self.add(brick)
                self.id_index[brick.id] = brick

            if self.capture_changes:
                self.changes.added.append(list(map(to_cbrick, pillow.bricks())))
            return pillow
        else:
            return None

    def __getitem__(self, item):
        if isinstance(item, Point):
            return self.bottle[item.x][item.y]
        if isinstance(item, Tuple):
            return self.bottle[item[0]][item[1]]
        return self.bottle[item]

    def __setitem__(self, key, value):
        if isinstance(key, Iterable):
            self.bottle[key[0]][key[1]] = value
            return
        self.bottle[key] = value

    def burn(self, *pillows: 'Pillow'):
        bricks = filter(lambda z: z, list(itertools.chain(*[p.bricks() for p in pillows])))
        return self.burn_bricks(bricks)

    def burn_bricks(self, bricks, max_count=4):
        t: Set[Point] = set()
        for b in bricks:
            t.update(self._burn(b, max_count))
        for point in t:
            self.kill_br(point)
        # print("end burn")
        # if sum(1 for Ys in self.bottle for x in Ys if x and x.is_virus()) != self.viruses:
        #    print("Here error")

        return t

    def kill_br(self, point):
        br: Brick = self[point]
        self[point] = None
        self.id_index.pop(br.id)
        br.kill()
        if self.capture_changes:
            self.changes.killed.append(to_cbrick(br))
        if br.is_virus():
            self.viruses = self.viruses - 1

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
        return falled

    def end(self, win: bool = True):
        self.empty()
        self.viruses = 0
        # my_font = pygame.font.SysFont('Comic Sans MS', 30)
        # text_surface = my_font.render('Done!', False, BLUE)
        self.add(Text("Win!" if win else "Loose", 30, BLUE, int(self.X * self.brick_size / 2),
                      int(self.Y * self.brick_size / 2)))
        # self.image = pygame.Surface([width, height])
        # self.image.fill(color)
        # self.image.set_colorkey(BLACK)

    def pause(self):
        self.add(self.pause_text)

    def unpause(self):
        self.pause_text.kill()

    def get_viruses(self):
        res = []
        for y in range(self.Y):
            for x in range(self.X):
                if self[x, y] and self[x, y].is_virus():
                    res.append(to_cbrick(self[x, y]).to_dict())
        return res

    def set_viruses(self, viruses):
        for virus in viruses:
            if not isinstance(virus, CBrick):
                virus = CBrick.from_dict(virus)
            b = to_br(virus, self.brick_size, self.offset)
            self.viruses = self.viruses + 1
            self[b.x, b.y] = b
            self.id_index[b.id] = b
            self.add(b)

    def register_moved(self, br: Brick):
        if self.capture_changes:
            self.changes.moved.append(to_cbrick(br))

    def pop_changes(self):
        res = self.changes
        self.changes = Changes()
        return res

    def apply_changes(self, changes_dict):
        # TODO change import
        from .pillow import Pillow
        changes: Changes = Changes.from_dict(changes_dict)
        for killed in changes.killed:
            br = self.id_index[killed.id]
            self.kill_br(Point(br.x, br.y))
        for added in changes.added:
            self.add_pillow(Pillow(
                to_br(added[0], self.brick_size, self.offset),
                to_br(added[1], self.brick_size, self.offset)
            ))
        for moved in changes.moved:
            br = self.id_index[moved.id]
            self[br.position] = None
            br.position = moved.position
            br.set_direction(Direction(moved.direction))
            self[br.position] = br


class Text(pygame.sprite.Sprite):
    def __init__(self, text, size, color, width, height):
        # Call the parent class (Sprite) constructor
        pygame.sprite.Sprite.__init__(self)

        self.font = pygame.font.SysFont("Comic Sans MS", size)
        self.textSurf = self.font.render(text, True, color)
        self.image = pygame.Surface((width, height))
        W = self.textSurf.get_width()
        H = self.textSurf.get_height()
        self.image.blit(self.textSurf, [width / 2 - W / 2, height / 2 - H / 2])
        self.rect = self.image.get_rect()


def to_cbrick(brick: Brick) -> CBrick:
    return CBrick(brick.id, brick.position, COLOR_NAMES[brick.color], virus=brick.virus,
                  direction=brick.direction.value if brick.direction else None)


def to_br(brick: CBrick, size, offset) -> Brick:
    return Brick(COLOR_SHORTS[brick.color], size, size, offset, id=brick.id, position=brick.position, virus=brick.virus,
                 direction=brick.direction)
