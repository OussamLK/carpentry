
from __future__ import annotations
import ortools.linear_solver.pywraplp
import ortools.linear_solver
from ortools.linear_solver import pywraplp
from dataclasses import dataclass
import ortools
import logging
from uuid import uuid1
solver = pywraplp.Solver.CreateSolver("SAT")
if not solver:
    raise Exception("solver has not been created")

type Variable = ortools.linear_solver.pywraplp.Variable
type Constraint = ortools.linear_solver.pywraplp.Constraint

infinity = solver.infinity()


def uuid():
    return str(uuid1())


@dataclass
class Board:
    height: int
    width: int
    saw_width: int

    def big_m(self) -> int:
        return max(self.height, self.width)*10


class Piece:
    id: int
    height: int
    width: int
    ly: Variable
    lx: Variable
    can_rotate: bool

    def __init__(self, id: int, height: int, width: int, board, can_rotate: bool = False):
        self.id = id
        self.height = height
        self.width = width
        self.board = board
        self.can_rotate = can_rotate
        self._create_in_board_constraint()

    def _create_in_board_constraint(self):
        self.lx = solver.IntVar(0.0, self.board.width -
                                self.width, f"lx_{self.id}")
        self.ly = solver.IntVar(
            0.0, self.board.height - self.height, f"ly_{self.id}")

    def __str__(self) -> str:
        return f"Piece({self.height}mm x {self.width}mm, can rotate: {self.can_rotate})"

    @staticmethod
    def parse_pieces(pieces: str, board) -> list[Piece]:
        '''expects a representation like `123,34 1200,340 900,340,r 230,340r`'''
        def parse_piece(id: int, p_str: str):
            tokens = p_str.split(',')
            height = int(tokens[0])
            width = int(tokens[1])
            can_rotate = len(tokens) >= 3 and tokens[2] == 'r'
            return Piece(id, height*10, width*10, board, can_rotate=can_rotate)
        return [parse_piece(id, p) for id, p in enumerate(pieces.split(" "))]

    def creat_non_overlapping_constraint(self, other: Piece):
        M = self.board.big_m()
        sw = self.board.saw_width
        v0, v1, v2, v3 = [self._decision_var(id) for id in range(4)]
        logging.debug(f"creating the constraint from piece {
            self.id} to piece {other.id}")
        piece_on_top = solver.Add(
            self.ly + self.height + sw <= other.ly + (1-v0)*M)  # type: ignore
        piece_to_left = solver.Add(
            self.lx + self.width + sw <= other.lx + (1-v1)*M)  # type: ignore
        piece_below = solver.Add(
            self.ly >= other.ly + other.height + sw - (1-v2)*M)  # type: ignore
        piece_to_right = solver.Add(
            self.lx >= other.lx + other.width + sw - (1-v3)*M)  # type: ignore
        at_least_one = solver.Add(v0+v1+v2+v3 >= 1)

    def filler_constraint(self, others: list[Piece]):
        M = self.board.big_m()
        sw = self.board.saw_width
        picked = self._decision_var(uuid())

        def create(other: Piece):
            v0, v1, v2, v3 = [self._decision_var(uuid()) for id in range(4)]
            logging.debug(f"creating the constraint from filler {
                          self.id} to piece {other.id}")
            piece_on_top = solver.Add(
                self.ly + self.height + sw <= other.ly +
                (1-v0)*M + (1-picked)*10*M
            )
            piece_to_left = solver.Add(
                self.lx + self.width + sw <= other.lx +
                (1-v1)*M + (1-picked)*10*M
            )
            piece_below = solver.Add(
                self.ly >= other.ly + other.height +
                sw - (1-v2)*M - (1-picked)*10*M
            )
            piece_to_right = solver.Add(
                self.lx >= other.lx + other.width +
                sw - (1-v3)*M - (1-picked)*10*M
            )
            at_least_one = solver.Add(v0+v1+v2+v3 >= 1)
        for other in others:
            create(other)
        return picked

    def _decision_var(self, id: str):
        import uuid
        return solver.IntVar(0.0, 1.0, str(uuid.uuid1()))
