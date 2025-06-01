from enum import Enum

class Direction(Enum):
    UP = (0, -1)  # 向上移动时y减小
    DOWN = (0, 1)  # 向下移动时y增加
    LEFT = (-1, 0)  # 向左移动时x减小
    RIGHT = (1, 0)  # 向右移动时x增加


    @classmethod
    def get_directions(cls) -> tuple:
        """返回包含所有方向值的元组"""
        return tuple(member.value for member in cls)
    @staticmethod
    def coordinates_to_direction(dx, dy):
        COORDINATES_TO_DIRECTION = {
            (0, -1): Direction.UP,
            (0, 1): Direction.DOWN,
            (-1, 0): Direction.LEFT,
            (1, 0): Direction.RIGHT
        }
        return COORDINATES_TO_DIRECTION.get((dx, dy))
