from .piece import Piece
from .board import Board
from .solution import Solution, Cutout
import logging
from ortools.linear_solver import pywraplp
import time
from uuid import uuid1


class SolverOpt:
    '''Checks if all the pieces fit inside the board'''
    pieces: list[Piece]
    board: Board

    def __init__(self, board: Board, pieces: list[Piece]):
        '''problem description format: `B:1200x800 S:2.5 450x300 500x600r 2x450x600`'''
        self.board = board
        logging.debug(f"Board has a saw width of: {board.saw_width}")
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

    def solve_opt(self, timeout_sec: float = 5) -> Solution:
        self._setup()
        if self.board.height > self.board.width:
            # self.solver.ClearObjective()
            lower_limit = self.lower_limit()
            self.solver.Minimize(lower_limit)
            start_time = time.time()
            self.solver.set_time_limit(int(timeout_sec*1000))
            status = self.solver.Solve()
            logging.debug(f"Optimization solver pass took {
                time.time()-start_time}")
            if status != pywraplp.Solver.OPTIMAL:
                logging.info("Returning suboptimal solution")
            cutouts = [Cutout(position_tl=(p.tly.solution_value()/10, p.tlx.solution_value()/10),
                              dimensions=(p.solution_height_tmm.solution_value()/10, p.solution_width_tmm.solution_value()/10)) for p in self.pieces
                       ]
            leftover = (Cutout(position_tl=(lower_limit.solution_value(
            )/10, 0), dimensions=(self.board.height-lower_limit.solution_value()/10, self.board.width)))
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
            rotated = self.solver.IntVar(
                0, 1, uuid()) if piece.can_rotate else None
            piece.initialize(tlx, tly, None, rotated)

    def create_inside_board_constraint(self, piece: Piece):
        '''The constraints so that the piece fits in the board'''

        self.solver.Add(piece.tlx + piece.solution_width_tmm <=
                        self.board.width_tmm)
        self.solver.Add(piece.tly + piece.solution_height_tmm <=
                        self.board.height_tmm)

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
