from __future__ import annotations
import re
import ortools.linear_solver.pywraplp
from .board import Board
from uuid import uuid1


class Piece:
    type Variable = ortools.linear_solver.pywraplp.Variable
    type Constraint = ortools.linear_solver.pywraplp.Constraint
    id: str
    height: float
    width: float
    tly: Variable
    tlx: Variable
    can_rotate: bool
    rotated: Variable
    initialized: bool

    def __init__(self, height: float, width: float, can_rotate: bool = False):
        self.id = uuid()
        self.height = height
        self.width = width
        self.can_rotate = can_rotate
        self.initialized = False

    @staticmethod
    def parse_piece(token: str) -> Piece:
        '''expects a representation like `12.5x34` or `23x34r` r mean can turn'''
        pattern = r"(?P<height>[0-9]+(\.[0-9]+)?)x(?P<width>[0-9]+(\.[0-9]+)?)(?P<can_rotate>r?)"
        regexp = re.compile(pattern)
        match = regexp.match(token)
        assert match, "Piece representation is not valid {token}"
        height, width, can_rotate = float(match['height']), float(
            match['width']), match['can_rotate'] == 'r'
        return Piece(height, width, can_rotate=can_rotate)

    def __repr__(self) -> str:
        return f"Piece({self.height:.1f}mm x {self.width:.1f}mm, can rotate: {self.can_rotate})"

    def __str__(self) -> str:
        return self.__repr__()

    def initialize(self, tlx, tly, picked, rotated):
        self.initialized = True
        self.tlx = tlx
        self.tly = tly
        self.picked = picked
        self.rotated = rotated

    @property
    def height_tmm(self):
        return int(self.height*10)

    @property
    def width_tmm(self):
        return int(self.width*10)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def solution_height_tmm(self):
        if self.can_rotate:
            return self.rotated*self.width_tmm + (1-self.rotated)*self.height_tmm
        else:
            return self.height_tmm + 0 * self.picked  # a hack to convert it to Variable

    @property
    def solution_width_tmm(self):
        if self.can_rotate:
            return self.rotated*self.height_tmm + (1-self.rotated)*self.width_tmm
        else:
            return self.width_tmm + 0 * self.picked  # a hack to convert it to variable


def uuid():
    return str(uuid1())
