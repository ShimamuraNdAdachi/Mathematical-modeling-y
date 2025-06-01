from typing import List, Tuple, Set
import heapq
from Direction import Direction
from Position import Position

class AStarPlanning:
    def __init__(self):
        pass

    @staticmethod
    def manhattan_distance_cal(position1: Position, position2: Position) -> int:
        return abs(position1.x-position2.x)+abs(position1.y-position2.y)

    def find_path(pos1: Position, pos2: Position, positions: Set, bounds: Tuple[int, int] = None) -> List[
        Position]:
        """
        使用A*算法寻找从pos1到pos2的路径，避开障碍物
        :param pos1: 起始位置
        :param pos2: 目标位置
        :param positions: 障碍物位置集合
        :param bounds: 边界限制，格式为(min_val, max_val)，表示x和y坐标都必须在[min_val, max_val]闭区间内
        :return: Position对象列表，表示路径
        """
        # 将障碍物位置转换为元组集合以便快速查找
        obstacles = positions

        # obstacles = {(pos.x, pos.y) for pos in positions}

        # 初始化open和closed集合
        open_set = []
        closed_set = set()
        came_from = {}

        # 使用坐标元组作为字典键
        start_tuple = (pos1.x, pos1.y)
        target_tuple = (pos2.x, pos2.y)

        # 检查起点和终点是否在边界内
        if bounds is not None:
            min_val, max_val = bounds
            if not (min_val <= pos1.x <= max_val and min_val <= pos1.y <= max_val and
                    min_val <= pos2.x <= max_val and min_val <= pos2.y <= max_val):
                print(f"警告：起点{pos1}或终点{pos2}超出边界范围[{min_val}, {max_val}]")
                return []

        # g_score记录从起点到当前点的实际代价
        g_score = {start_tuple: 0}
        # f_score记录估计的总代价
        f_score = {start_tuple: AStarPlanning.manhattan_distance_cal(pos1, pos2)}

        # 将起点加入open集合
        heapq.heappush(open_set, (f_score[start_tuple], start_tuple))

        while open_set:
            current_tuple = heapq.heappop(open_set)[1]

            if current_tuple == target_tuple:
                return AStarPlanning._reconstruct_path_with_positions(came_from, current_tuple)

            closed_set.add(current_tuple)

            # 检查所有可能的移动方向
            for dx, dy in Direction.get_directions():
                new_x = current_tuple[0] + dx
                new_y = current_tuple[1] + dy

                # 检查新位置是否在边界内
                if bounds is not None:
                    min_val, max_val = bounds
                    if not (min_val <= new_x <= max_val and min_val <= new_y <= max_val):
                        continue

                neighbor_tuple = (new_x, new_y)

                # 跳过已经检查过的位置和障碍物位置
                if neighbor_tuple in closed_set or neighbor_tuple in obstacles:
                    continue

                tentative_g_score = g_score[current_tuple] + 1

                if neighbor_tuple not in g_score or tentative_g_score < g_score[neighbor_tuple]:
                    came_from[neighbor_tuple] = current_tuple
                    g_score[neighbor_tuple] = tentative_g_score
                    neighbor_pos = Position(new_x, new_y)
                    f_score[neighbor_tuple] = g_score[neighbor_tuple] + AStarPlanning.manhattan_distance_cal(
                        neighbor_pos, pos2)
                    heapq.heappush(open_set, (f_score[neighbor_tuple], neighbor_tuple))

        return []  # 没有找到路径

    @staticmethod
    def find_path_1(pos1: Position, pos2: Position, positions: Set[Position], bounds: Tuple[int, int] = None) -> List[
        Position]:
        """
        使用A*算法寻找从pos1到pos2的路径，避开障碍物
        :param pos1: 起始位置
        :param pos2: 目标位置
        :param positions: 障碍物位置集合
        :param bounds: 边界限制，格式为(min_val, max_val)，表示x和y坐标都必须在[min_val, max_val]闭区间内
        :return: Position对象列表，表示路径
        """
        # 如果起点和终点相同，返回空路径
        if pos1.x == pos2.x and pos1.y == pos2.y:
            return []

        # 将障碍物位置转换为元组集合以便快速查找
        obstacles = set()
        for pos in positions:
            obstacles.add(pos)

        # 初始化open和closed集合
        open_set = []
        closed_set = set()
        came_from = {}

        # 使用坐标元组作为字典键
        start_tuple = (pos1.x, pos1.y)
        target_tuple = (pos2.x, pos2.y)

        # 检查起点和终点是否在边界内
        if bounds is not None:
            min_val, max_val = bounds
            if not (min_val <= pos1.x <= max_val and min_val <= pos1.y <= max_val and
                    min_val <= pos2.x <= max_val and min_val <= pos2.y <= max_val):
                print(f"警告：起点{pos1}或终点{pos2}超出边界范围[{min_val}, {max_val}]")
                return []

        # 检查起点和终点是否被障碍物占据
        # if start_tuple in obstacles or target_tuple in obstacles:
        #     print(f"警告：起点{pos1}或终点{pos2}被障碍物占据")
        #     return []

        # g_score记录从起点到当前点的实际代价
        g_score = {start_tuple: 0}
        # f_score记录估计的总代价
        f_score = {start_tuple: AStarPlanning.manhattan_distance_cal(pos1, pos2)}

        # 将起点加入open集合
        heapq.heappush(open_set, (f_score[start_tuple], start_tuple))

        while open_set:
            current_tuple = heapq.heappop(open_set)[1]

            if current_tuple == target_tuple:
                path = AStarPlanning._reconstruct_path_with_positions_1(came_from, current_tuple)
                if not path:  # 如果重建路径失败
                    print(f"警告：找到目标但无法重建路径，从{pos1}到{pos2}")
                return path

            closed_set.add(current_tuple)

            # 检查所有可能的移动方向
            for dx, dy in Direction.get_directions():
                new_x = current_tuple[0] + dx
                new_y = current_tuple[1] + dy

                # 检查新位置是否在边界内
                if bounds is not None:
                    min_val, max_val = bounds
                    if not (min_val <= new_x <= max_val and min_val <= new_y <= max_val):
                        continue

                neighbor_tuple = (new_x, new_y)

                # 跳过已经检查过的位置和障碍物位置
                if neighbor_tuple in closed_set or neighbor_tuple in obstacles:
                    continue

                tentative_g_score = g_score[current_tuple] + 1

                if neighbor_tuple not in g_score or tentative_g_score < g_score[neighbor_tuple]:
                    came_from[neighbor_tuple] = current_tuple
                    g_score[neighbor_tuple] = tentative_g_score
                    neighbor_pos = Position(new_x, new_y)
                    f_score[neighbor_tuple] = g_score[neighbor_tuple] + AStarPlanning.manhattan_distance_cal(
                        neighbor_pos, pos2)
                    heapq.heappush(open_set, (f_score[neighbor_tuple], neighbor_tuple))

        print(f"警告：无法找到从{pos1}到{pos2}的路径")
        return []  # 没有找到路径
    @staticmethod
    def _reconstruct_path_with_positions(came_from: dict, current: Tuple[int, int]) -> List[Position]:
        """
        重建从起点到终点的路径，返回Position对象列表
        """
        global p
        path = [Position(current[0], current[1])]
        while current in came_from:
            current = came_from[current]
            path.append(Position(current[0], current[1]))
            p = path[::-1]
            del p[0]
        return p  # 反转路径，使其从起点开始

    @staticmethod
    def _reconstruct_path_with_positions_1(came_from: dict, current: Tuple[int, int]) -> List[Position]:
        """
        重建从起点到终点的路径，返回Position对象列表
        """
        path = []
        while current in came_from:
            path.append(Position(current[0], current[1]))
            current = came_from[current]

        # 添加起点
        path.append(Position(current[0], current[1]))

        # 反转路径，使其从起点开始
        path = path[::-1]

        # 如果路径至少有两个点，移除起点（因为机器人已经在起点上）
        if len(path) >= 2:
            path = path[1:]

        return path

