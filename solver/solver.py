from __future__ import annotations
import re
import ortools.linear_solver.pywraplp
import ortools.linear_solver
from ortools.linear_solver import pywraplp
import ortools
from dataclasses import dataclass
import logging
from uuid import uuid1
from .piece import Piece
from .board import Board
import time


@dataclass
class Solution:
    cutouts: list[Cutout]
    leftover: list[Cutout]
    unfits: list[Cutout]
    board: Board


@dataclass(frozen=True)
class Cutout:
    position_tl: tuple[float, float]
    dimensions: tuple[float, float]

    @property
    def straightened_dimensions(self) -> tuple[float, float]:
        '''to compare piece in test output the piece is straighened'''
        h, w = self.dimensions
        return (h, w) if h > w else (w, h)


class Solver:

    def __init__(self, height: float, width: float, saw_width: float, pieces: list[Piece]):
        '''problem description format: `B:1200x800 S:2.5 450x300 500x600r 2x450x600`'''
        self.board = Board(height, width, saw_width)
        self.pieces = pieces

    @staticmethod
    def from_str(problem_description: str):
        desc = Solver._parse_description(problem_description)
        assert isinstance(desc['height'], float)
        assert isinstance(desc['width'], float)
        assert isinstance(desc['saw_width'], float)
        assert isinstance(desc['pieces'], list)
        pieces = desc['pieces']
        solver = Solver(desc['height'], desc['width'],
                        desc['saw_width'], pieces)
        return solver

    @staticmethod
    def _parse_description(desc: str):
        [board, saw, *pieces] = desc.split()
        assert board.startswith(
            'B:'), "Board description should start with a `B:...`"
        dims = board[2:].split('x')
        assert len(dims), f"You should have 2 dimensions for the board but got {
            dims}"
        height, width = [float(dim) for dim in dims]
        assert saw.startswith(
            "S:"), 'Second entry in problem description should be S:<saw width>'
        saw_width = float(saw[2:])
        pieces = [Piece.parse_piece(piece) for piece in pieces]
        return dict(height=height, width=width, saw_width=saw_width, pieces=pieces)

    def solve(self) -> Solution:
        solution = SolverFit(self.board, self.pieces)._fit_pieces()
        n_picked = len(solution.cutouts)
        if n_picked < len(self.pieces):
            return solution
        solver_opt = SolverOpt(self.board, self.pieces)
        return solver_opt.solve_opt()


class SolverFit:
    '''Checks if all the pieces fit inside the board'''
    pieces: list[Piece]
    board: Board

    def __init__(self, board: Board, pieces: list[Piece]):
        '''problem description format: `B:1200x800 S:2.5 450x300 500x600r 2x450x600`'''
        self.board = board
        self.pieces = pieces
        self._setup()

    def _setup(self):
        self._setup_solver()
        self._initialize_pieces()
        for piece in self.pieces:
            self.create_inside_board_constraint(piece)
        for i, p1 in enumerate(self.pieces):
            for p2 in self.pieces[i+1:]:
                self._add_constraints(p1, p2)

    def _fit_pieces(self):
        objective = self.solver.Sum(
            piece.area*piece.picked for piece in self.pieces)
        self.solver.Maximize(objective)
        start_time = time.time()
        status = self.solver.Solve()
        logging.debug(f"First solver pass took {time.time() - start_time}")
        if status != pywraplp.Solver.OPTIMAL:
            raise Exception(
                "fit_pieces phase did not finish excuting, solver status not optimal")
        n_picked = sum(
            p.picked.solution_value() for p in self.pieces)
        print(f"picked {int(n_picked)}")
        cutouts: list[Cutout] = [Cutout(position_tl=(p.tly.solution_value()/10, p.tlx.solution_value()/10), dimensions=(
            # if p.picked.solution_value() >= .5]
            p.solution_height_tmm.solution_value()/10, p.solution_width_tmm.solution_value()/10)) for p in self.pieces
            if p.picked.solution_value() > .5
        ]
        unfit: list[Cutout] = [Cutout(position_tl=(p.tly.solution_value()/10, p.tlx.solution_value()/10), dimensions=(
            # if p.picked.solution_value() >= .5]
            p.solution_height_tmm.solution_value()/10, p.solution_width_tmm.solution_value()/10)) for p in self.pieces
            if p.picked.solution_value() < .5
        ]
        solution = Solution(cutouts=cutouts, leftover=[],
                            unfits=unfit, board=self.board)
        return solution

    def _setup_solver(self):
        solver = pywraplp.Solver.CreateSolver("CP-SAT")
        if not solver:
            raise Exception("solver has not been created")
        self.solver = solver
        self.infinity = self.solver.infinity()

    def _initialize_pieces(self):
        for piece in self.pieces:
            tlx, tly = [self.solver.NumVar(
                0, self.infinity, uuid()) for _ in range(2)]
            picked = self.solver.IntVar(0, 1, uuid())
            rotated = self.solver.IntVar(
                0, 1, uuid()) if piece.can_rotate else None
            piece.initialize(tlx, tly, picked, rotated)

    def create_inside_board_constraint(self, piece: Piece):
        '''The constraints so that the piece fits in the board'''

        self.solver.Add(piece.tlx + piece.solution_width_tmm <=
                        self.board.width_tmm + self.board.big_m()*(1-piece.picked))
        self.solver.Add(piece.tly + piece.solution_height_tmm <=
                        self.board.height_tmm + self.board.big_m()*(1-piece.picked))

    def _add_constraints(self, p1: Piece,  p2: Piece):
        M = self.board.big_m()
        sw = self.board.saw_width_tmm
        v0, v1, v2, v3 = [self._decision_var() for _ in range(4)]
        piece_on_top = p1.tly + p1.solution_height_tmm + \
            sw <= p2.tly + (1-v0)*M  # type: ignore
        piece_to_left = p1.tlx + p1.solution_width_tmm + \
            sw <= p2.tlx + (1-v1)*M  # type: ignore
        piece_below = p1.tly >= p2.tly + \
            p2.solution_height_tmm + sw - (1-v2)*M  # type: ignore
        piece_to_right = p1.tlx >= p2.tlx + \
            p2.solution_width_tmm + sw - (1-v3)*M  # type: ignore
        at_least_one = v0+v1+v2+v3 >= 1
        cs = [piece_on_top, piece_below, piece_to_left,
              piece_to_right, at_least_one]  # type: ignore
        for c in cs:
            self.solver.Add(c)

    def lower_limit(self):
        '''The height of the entire cutouts to minimize'''
        lower_limit = self.solver.NumVar(0, self.board.height*10, uuid())
        for p in self.pieces:
            self.solver.Add(lower_limit >= p.tly + p.solution_height_tmm)
        return lower_limit

    def rightmost_limit(self):
        '''The height of the entire cutouts to minimize'''
        rightmost_limit = self.solver.NumVar(0, self.board.width*10, uuid())
        for p in self.pieces:
            self.solver.Add(rightmost_limit >= p.tlx + p.solution_width_tmm)
        return rightmost_limit

    def _decision_var(self):
        return self.solver.IntVar(0.0, 1.0, str(uuid1()))


class SolverOpt:
    '''Checks if all the pieces fit inside the board'''
    pieces: list[Piece]
    board: Board

    def __init__(self, board: Board, pieces: list[Piece]):
        '''problem description format: `B:1200x800 S:2.5 450x300 500x600r 2x450x600`'''
        self.board = board
        self.pieces = pieces
        self._setup()

    def _setup(self):
        self._setup_solver()
        self._initialize_pieces()
        for piece in self.pieces:
            self.create_inside_board_constraint(piece)
        for i, p1 in enumerate(self.pieces):
            for p2 in self.pieces[i+1:]:
                self._add_constraints(p1, p2)

    def solve_opt(self) -> Solution:
        self._setup()
        picked_vars = [p.picked for p in self.pieces]
        self.solver.Add(self.solver.Sum(
            picked_vars) >= len(self.pieces))
        if self.board.height > self.board.width:
            # self.solver.ClearObjective()
            lower_limit = self.lower_limit()
            self.solver.Minimize(lower_limit)
            start_time = time.time()
            status = self.solver.Solve()
            logging.debug(f"Second solver pass took {
                time.time()-start_time}")
            if status != pywraplp.Solver.OPTIMAL:
                raise Exception(f"something fishy going on {status=}")
            cutouts = [Cutout(position_tl=(p.tly.solution_value()/10, p.tlx.solution_value()/10),
                              dimensions=(p.solution_height_tmm.solution_value()/10, p.solution_width_tmm.solution_value()/10)) for p in self.pieces
                       ]
            leftover = (Cutout(position_tl=(lower_limit.solution_value(
            )/10, 0), dimensions=(self.board.height-lower_limit.solution_value()/10, self.board.width)))
            n_picked = sum(piece.picked.solution_value()
                           for piece in self.pieces)
            print(f"second pass picked {n_picked}")
            return Solution(cutouts=cutouts, unfits=[], leftover=[leftover], board=self.board)
        else:
            # self.solver.ClearObjective()
            rightmost_limit = self.rightmost_limit()
            self.solver.Minimize(rightmost_limit)
            self.solver.Solve()
            cutouts = [Cutout(position_tl=(p.tly.solution_value()/10, p.tlx.solution_value()/10),
                              dimensions=(p.solution_height_tmm.solution_value()/10, p.solution_width_tmm.solution_value()/10)) for p in self.pieces
                       ]
            leftover = (Cutout(position_tl=(0, rightmost_limit.solution_value()/10), dimensions=(
                self.board.height, self.board.width-rightmost_limit.solution_value()/10)))
            return Solution(cutouts=cutouts, unfits=[], leftover=[leftover], board=self.board)

    def _setup_solver(self):
        solver = pywraplp.Solver.CreateSolver("CP-SAT")
        if not solver:
            raise Exception("solver has not been created")
        self.solver = solver
        self.infinity = self.solver.infinity()

    def _initialize_pieces(self):
        for piece in self.pieces:
            tlx, tly = [self.solver.NumVar(
                0, self.infinity, uuid()) for _ in range(2)]
            picked = self.solver.IntVar(0, 1, uuid())
            rotated = self.solver.IntVar(
                0, 1, uuid()) if piece.can_rotate else None
            piece.initialize(tlx, tly, picked, rotated)

    def create_inside_board_constraint(self, piece: Piece):
        '''The constraints so that the piece fits in the board'''

        self.solver.Add(piece.tlx + piece.solution_width_tmm <=
                        self.board.width_tmm + self.board.big_m()*(1-piece.picked))
        self.solver.Add(piece.tly + piece.solution_height_tmm <=
                        self.board.height_tmm + self.board.big_m()*(1-piece.picked))

    def _add_constraints(self, p1: Piece,  p2: Piece):
        M = self.board.big_m()
        sw = self.board.saw_width_tmm
        v0, v1, v2, v3 = [self._decision_var() for _ in range(4)]
        piece_on_top = p1.tly + p1.solution_height_tmm + \
            sw <= p2.tly + (1-v0)*M  # type: ignore
        piece_to_left = p1.tlx + p1.solution_width_tmm + \
            sw <= p2.tlx + (1-v1)*M  # type: ignore
        piece_below = p1.tly >= p2.tly + \
            p2.solution_height_tmm + sw - (1-v2)*M  # type: ignore
        piece_to_right = p1.tlx >= p2.tlx + \
            p2.solution_width_tmm + sw - (1-v3)*M  # type: ignore
        at_least_one = v0+v1+v2+v3 >= 1
        cs = [piece_on_top, piece_below, piece_to_left,
              piece_to_right, at_least_one]  # type: ignore
        for c in cs:
            self.solver.Add(c)

    def lower_limit(self):
        '''The height of the entire cutouts to minimize'''
        lower_limit = self.solver.NumVar(0, self.board.height*10, uuid())
        for p in self.pieces:
            self.solver.Add(lower_limit >= p.tly + p.solution_height_tmm)
        return lower_limit

    def rightmost_limit(self):
        '''The height of the entire cutouts to minimize'''
        rightmost_limit = self.solver.NumVar(0, self.board.width*10, uuid())
        for p in self.pieces:
            self.solver.Add(rightmost_limit >= p.tlx + p.solution_width_tmm)
        return rightmost_limit

    def _decision_var(self):
        return self.solver.IntVar(0.0, 1.0, str(uuid1()))


def uuid():
    return str(uuid1())
