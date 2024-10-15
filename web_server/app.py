from fastapi import FastAPI
from . import schemata
from solver import Solver, Piece as SolverPiece
import base64
from illustrate import BoardIllustrator
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=[
                   '*'], allow_methods=['*'], allow_headers=['*'])


@app.get('/')
def index():
    return "hello from fastapi"


@app.post('/problems')
def create_problem(problem: schemata.Problem):
    pieces: list[SolverPiece] = [SolverPiece(
        p.height, p.width, p.canRotate) for p in problem.pieces]
    solver = Solver(problem.board.height, problem.board.width,
                    problem.sawWidth, pieces)
    solution = solver.solve()
    illustrator = BoardIllustrator(problem.board.height, problem.board.width)
    for cutout in solution.cutouts:
        illustrator.add_cutout(
            cutout.position_tl[0], cutout.position_tl[1], cutout.dimensions[0], cutout.dimensions[1], color='#eaeaea', text_color='black')
    for leftover in solution.leftover:
        illustrator.add_leftover(
            leftover.position_tl[0], leftover.position_tl[1], leftover.dimensions[0], leftover.dimensions[1], color='white', text_color='black')
    print_illustrator = BoardIllustrator(
        problem.board.height, problem.board.width)
    for cutout in solution.cutouts:
        print_illustrator.add_cutout(
            cutout.position_tl[0], cutout.position_tl[1], cutout.dimensions[0], cutout.dimensions[1], color='#eaeaea', text_color='black')
    for leftover in solution.leftover:
        print_illustrator.add_cutout(
            leftover.position_tl[0], leftover.position_tl[1], leftover.dimensions[0], leftover.dimensions[1], color='white', text_color='black')
    b64 = base64.b64encode(illustrator.get_image()).decode('utf-8')
    print_b64 = base64.b64encode(print_illustrator.get_image()).decode('utf-8')
    unfits = [{"height": unfit.dimensions[0], "width": unfit.dimensions[1]}
              for unfit in solution.unfits]
    return dict(illustration=b64, cutouts=solution.cutouts, leftover=solution.leftover, unfits=unfits, printIllustration=print_b64)
