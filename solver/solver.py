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
from .solution import Solution, Cutout
from .solver_opt import SolverOpt


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

    def solve(self, timeout_sec: float = 5) -> Solution:
        solution = SolverFit(self.board, self.pieces)._fit_pieces(
            timeout_sec=timeout_sec)
        n_picked = len(solution.cutouts)
        if n_picked < len(self.pieces):
            return solution
        solver_opt = SolverOpt(self.board, self.pieces)
        return solver_opt.solve_opt(timeout_sec=timeout_sec)


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

    def _fit_pieces(self, timeout_sec: float = 5):
        objective = self.solver.Sum(
            piece.area*piece.picked for piece in self.pieces)
        self.solver.Maximize(objective)
        start_time = time.time()
        self.solver.set_time_limit(int(timeout_sec*1000))
        status = self.solver.Solve()
        logging.debug(f"First solver pass took {time.time() - start_time}")
        if status != pywraplp.Solver.OPTIMAL:
            logging.info("solver fit not optimal")
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


def uuid():
    return str(uuid1())
