from pydantic import BaseModel


class CreatePiece(BaseModel):
    height: float
    width: float
    can_rotate: bool


class Piece(BaseModel):
    id: int
    height: float
    width: float
    can_rotate: bool


class Cutout(BaseModel):
    top_left_y: float
    top_right_y: float
    piece: Piece


class Board(BaseModel):
    height: float
    width: float


class Problem(BaseModel):
    board: Board
    saw_width: float
    pieces: list[CreatePiece]
