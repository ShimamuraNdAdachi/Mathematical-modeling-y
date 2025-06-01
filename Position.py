from dataclasses import dataclass


@dataclass
class Position():
    x: int
    y: int

    def __hash__(self):
        # 使用坐标的元组生成哈希值
        return hash((self.x, self.y))

    def __add__(self, other):
        x, y = other
        return Position(self.x + x, self.y + y)

    def __eq__(self, other):
        if not isinstance(other, Position):
            return False
        return self.x == other.x and self.y == other.y
