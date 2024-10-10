from dataclasses import dataclass


@dataclass
class Board:
    height: float
    width: float
    saw_width: float

    def big_m(self) -> int:
        return max(self.height_tmm, self.width_tmm)*10

    @property
    def height_tmm(self) -> int:
        return int(self.height*10)

    @property
    def width_tmm(self) -> int:
        return int(self.width*10)

    @property
    def saw_width_tmm(self) -> int:
        return int(self.saw_width*10)
