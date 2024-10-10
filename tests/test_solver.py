import pytest

from solver import Solver


def test_parser():
    problem_str = "B:1000x2000 S:2.5 23.5x33 3x34.5r 200x300r"
    d = Solver._parse_description(problem_str)
    assert d['height'] == 1000
    assert d['width'] == 2000
    assert d['saw_width'] == 2.5
    assert isinstance(d['pieces'], list)
    assert len(d['pieces']) == 3
