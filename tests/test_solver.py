import pytest

from solver import Solver
from solver.solver import SolverFit, Board
import pickle


@pytest.fixture
def test_cases():
    with open('tests/pickled_solver_test_cases.bin', 'rb') as f:
        test_cases = pickle.load(f)
    return test_cases


def test_parser():
    problem_str = "B:1000x2000 S:2.5 23.5x33 3x34.5r 200x300r"
    d = Solver._parse_description(problem_str)
    assert d['height'] == 1000
    assert d['width'] == 2000
    assert d['saw_width'] == 2.5
    assert isinstance(d['pieces'], list)
    assert len(d['pieces']) == 3


def test_solver(test_cases):
    for test_case in test_cases:
        problem, reference_solution = test_case['problem'], test_case['solution']
        current_solution = Solver(**problem).solve()
        assert len(current_solution.unfits) == len(
            reference_solution.unfits)
        if current_solution.leftover:
            assert current_solution.leftover[0].dimensions == reference_solution.leftover[0].dimensions
        assert set(c.straightened_dimensions for c in reference_solution.cutouts) == set(
            c.straightened_dimensions for c in current_solution.cutouts)


def test_fit_pieces_solver(test_cases):
    for test_case in test_cases:
        problem, reference_solution = test_case['problem'], test_case['solution']
        fit_solution = SolverFit(
            Board(height=problem['height'], width=problem['width'], saw_width=problem['saw_width']), problem['pieces']).solve()
        # comparing by area because pices solution of problems that have same area pieces are random
        assert set(s.dimensions[0]*s.dimensions[1] for s in fit_solution.unfits) == set(
            s.dimensions[0]*s.dimensions[1] for s in reference_solution.unfits)
