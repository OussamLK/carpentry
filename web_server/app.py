from fastapi import FastAPI
from . import schemata
from solver import Solver, Piece as SolverPiece
import base64
from illustrate import BoardIllustrator

app = FastAPI()


@app.get('/')
def index():
    return "hello from fastapi"


@app.post('/problems')
def create_problem(problem: schemata.Problem) -> str:
    pieces: list[SolverPiece] = [SolverPiece(
        p.height, p.width, p.can_rotate) for p in problem.pieces]
    solver = Solver(problem.board.height, problem.board.width,
                    problem.saw_width, pieces)
    solution = solver.solve()
    illustrator = BoardIllustrator(problem.board.height, problem.board.width)
    for cutout in solution.cutouts:
        illustrator.add_cutout(
            cutout.position_tl[0], cutout.position_tl[1], cutout.dimensions[0], cutout.dimensions[1])
    for leftover in solution.leftover:
        illustrator.add_leftover(
            leftover.position_tl[0], leftover.position_tl[1], leftover.dimensions[0], leftover.dimensions[1])
    b64 = base64.b64encode(illustrator.get_image()).decode('utf-8')
    return f'''<html><body><img src=""data:image/png;base64,{b64}"></img></body></html>'''
