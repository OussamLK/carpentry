from pydantic import BaseModel


class CreatePiece(BaseModel):
    height: float
    width: float
    canRotate: bool


class Piece(BaseModel):
    id: int
    height: float
    width: float
    canRotate: bool


class Cutout(BaseModel):
    top_left_y: float
    top_right_y: float
    piece: Piece


class Board(BaseModel):
    height: float
    width: float


class Problem(BaseModel):
    board: Board
    sawWidth: float
    pieces: list[CreatePiece]
