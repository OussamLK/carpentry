from __future__ import annotations
from dataclasses import dataclass
from .board import Board


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
