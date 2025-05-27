from enum import Enum

class Direction(Enum):
    UP = (0, -1)  # 向上移动时y减小
    DOWN = (0, 1)  # 向下移动时y增加
    LEFT = (-1, 0)  # 向左移动时x减小
    RIGHT = (1, 0)  # 向右移动时x增加