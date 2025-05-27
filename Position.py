from dataclasses import dataclass

@dataclass
class Position:
    x: int
    y: int

    def __add__(self, other):
        return Position(self.x + other[0], self.y + other[1])

    def __eq__(self, other):
        if not isinstance(other, Position):
            return False
        return self.x == other.x and self.y == other.y
