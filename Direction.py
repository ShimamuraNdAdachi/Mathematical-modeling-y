from enum import Enum

class Direction(Enum):
    UP = (0, -1)  # 向上移动时y减小
    DOWN = (0, 1)  # 向下移动时y增加
    LEFT = (-1, 0)  # 向左移动时x减小
    RIGHT = (1, 0)  # 向右移动时x增加

    LIST = [UP, DOWN, LEFT, RIGHT]
    COORDINATES_TO_DIRECTION = {
        (0, -1): UP,
        (0, 1): DOWN,
        (-1, 0): LEFT,
        (1, 0): RIGHT
    }
    @staticmethod
    def coordinates_to_direction(dx, dy):
        return Direction.COORDINATES_TO_DIRECTION.get((dx, dy))
