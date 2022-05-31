from dataclasses import dataclass, field
from typing import List, Tuple

from mashumaro import DataClassDictMixin


@dataclass
class CBrick(DataClassDictMixin):
    id: int
    position: List = field(default_factory=[None, None])
    color: str = None
    virus: bool = False

    def __setitem__(self, key, value):
        if isinstance(key, Tuple):
            self.position[0] = value[0]
            self.position[1] = value[1]
            return
        self.position = list(value)

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


@dataclass
class Changes(DataClassDictMixin):
    added: List[List[CBrick]] = field(default_factory=list)
    moved: List[CBrick] = field(default_factory=list)
    killed: List[CBrick] = field(default_factory=list)

    def has_changes(self):
        return self.added or self.moved or self.killed
