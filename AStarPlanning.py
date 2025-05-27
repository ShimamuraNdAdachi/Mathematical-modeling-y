from typing import List, Tuple
import heapq
from Direction import Direction
from Position import Position

class AStarPlanning:
    def __init__(self):
        pass

    @staticmethod
    def manhattan_distance_cal(position1: Position, position2: Position) -> int:
        return abs(position1.x-position2.x)+abs(position1.y-position2.y)

    def find_path(self, position1: Position, position2: Position) -> List[Position]:
        """
        使用A*算法寻找从position1到position2的路径
        :param position1: 起始位置
        :param position2: 目标位置
        :return: Position对象列表，表示路径
        """
        # 初始化open和closed集合
        open_set = []
        closed_set = set()
        came_from = {}

        # 使用坐标元组作为字典键
        start_tuple = (position1.x, position1.y)
        target_tuple = (position2.x, position2.y)

        # g_score记录从起点到当前点的实际代价
        g_score = {start_tuple: 0}
        # f_score记录估计的总代价
        f_score = {start_tuple: self.manhattan_distance_cal(position1, position2)}

        # 将起点加入open集合
        heapq.heappush(open_set, (f_score[start_tuple], start_tuple))

        while open_set:
            current_tuple = heapq.heappop(open_set)[1]

            if current_tuple == target_tuple:
                return self._reconstruct_path_with_positions(came_from, current_tuple)

            closed_set.add(current_tuple)

            # 检查所有可能的移动方向
            for dx, dy in Direction:
                new_x = current_tuple[0] + dx
                new_y = current_tuple[1] + dy
                neighbor_tuple = (new_x, new_y)

                if neighbor_tuple in closed_set:
                    continue

                tentative_g_score = g_score[current_tuple] + 1

                if neighbor_tuple not in g_score or tentative_g_score < g_score[neighbor_tuple]:
                    came_from[neighbor_tuple] = current_tuple
                    g_score[neighbor_tuple] = tentative_g_score
                    neighbor_pos = Position(new_x, new_y)
                    f_score[neighbor_tuple] = g_score[neighbor_tuple] + self.manhattan_distance_cal(neighbor_pos,
                                                                                                    position2)
                    heapq.heappush(open_set, (f_score[neighbor_tuple], neighbor_tuple))

        return []  # 没有找到路径

    @staticmethod
    def _reconstruct_path_with_positions(came_from: dict, current: Tuple[int, int]) -> List[Position]:
        """
        重建从起点到终点的路径，返回Position对象列表
        """
        path = [Position(current[0], current[1])]
        while current in came_from:
            current = came_from[current]
            path.append(Position(current[0], current[1]))
        return path[::-1]  # 反转路径，使其从起点开始


