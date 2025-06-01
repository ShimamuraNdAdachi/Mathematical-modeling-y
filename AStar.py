from typing import List, Set, Tuple, Dict
import heapq
from dataclasses import dataclass
from Position import Position


@dataclass
class Node:
    """节点类，用于A*算法"""
    position: Position  # 节点位置
    g_cost: float  # 从起点到当前节点的实际代价
    h_cost: float  # 从当前节点到终点的估计代价
    parent: 'Node'  # 父节点

    @property
    def f_cost(self) -> float:
        """f(n) = g(n) + h(n)"""
        return self.g_cost + self.h_cost

    def __lt__(self, other: 'Node') -> bool:
        """用于优先队列的比较"""
        return self.f_cost < other.f_cost


class AStar:
    def __init__(self):
        # 四个方向：上、右、下、左
        self.directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]

    @staticmethod
    def manhattan_distance(pos1: Position, pos2: Position) -> float:
        """计算曼哈顿距离"""
        return abs(pos1.x - pos2.x) + abs(pos1.y - pos2.y)

    @staticmethod
    def euclidean_distance(pos1: Position, pos2: Position) -> float:
        """计算欧几里得距离"""
        return ((pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2) ** 0.5

    def is_valid_position(self, pos: Position, bounds: Tuple[int, int]) -> bool:
        """检查位置是否在边界内"""
        min_val, max_val = bounds
        return min_val <= pos.x <= max_val and min_val <= pos.y <= max_val

    def get_neighbors(self, node: Node, bounds: Tuple[int, int], obstacles: Set[Tuple[int, int]]) -> List[Position]:
        """获取相邻的可行节点"""
        neighbors = []
        for dx, dy in self.directions:
            new_x = node.position.x + dx
            new_y = node.position.y + dy
            new_pos = Position(new_x, new_y)

            # 检查是否在边界内且不是障碍物
            if (self.is_valid_position(new_pos, bounds) and
                    (new_pos.x, new_pos.y) not in obstacles):
                neighbors.append(new_pos)
        return neighbors

    def find_path(self, start: Position, goal: Position,
                  obstacles: Set[Position], bounds: Tuple[int, int]) -> List[Position]:
        """
        A*寻路算法主函数
        :param start: 起点
        :param goal: 终点
        :param obstacles: 障碍物集合
        :param bounds: 边界范围 (min_val, max_val)
        :return: 路径列表，从起点到终点（不包含起点）
        """
        # 如果起点和终点相同
        if start == goal:
            return []

        # 转换障碍物为坐标元组集合
        obstacle_tuples = {(obs.x, obs.y) for obs in obstacles}

        # 检查起点和终点是否有效
        if not self.is_valid_position(start, bounds) or not self.is_valid_position(goal, bounds):
            print(f"警告：起点{start}或终点{goal}超出边界范围{bounds}")
            return []

        if (start.x, start.y) in obstacle_tuples or (goal.x, goal.y) in obstacle_tuples:
            print(f"警告：起点{start}或终点{goal}位于障碍物上")
            return []

        # 初始化开启和关闭列表
        open_list = []
        closed_set = set()

        # 创建起始节点
        start_node = Node(
            position=start,
            g_cost=0,
            h_cost=self.manhattan_distance(start, goal),
            parent=None
        )

        # 将起始节点加入开启列表
        heapq.heappush(open_list, start_node)
        node_dict = {(start.x, start.y): start_node}  # 用于快速查找节点

        while open_list:
            # 获取f值最小的节点
            current = heapq.heappop(open_list)
            current_tuple = (current.position.x, current.position.y)

            # 如果到达目标
            if current.position == goal:
                path = []
                while current.parent is not None:
                    path.append(current.position)
                    current = current.parent
                return path[::-1]  # 反转路径并返回

            # 将当前节点加入关闭列表
            closed_set.add(current_tuple)

            # 检查所有相邻节点
            for neighbor_pos in self.get_neighbors(current, bounds, obstacle_tuples):
                neighbor_tuple = (neighbor_pos.x, neighbor_pos.y)

                # 如果节点已经在关闭列表中，跳过
                if neighbor_tuple in closed_set:
                    continue

                # 计算新的g值
                new_g_cost = current.g_cost + 1

                # 如果是新节点或找到了更好的路径
                if (neighbor_tuple not in node_dict or
                        new_g_cost < node_dict[neighbor_tuple].g_cost):
                    # 创建新的相邻节点
                    neighbor_node = Node(
                        position=neighbor_pos,
                        g_cost=new_g_cost,
                        h_cost=self.manhattan_distance(neighbor_pos, goal),
                        parent=current
                    )

                    # 更新或添加到节点字典
                    node_dict[neighbor_tuple] = neighbor_node

                    # 添加到开启列表
                    heapq.heappush(open_list, neighbor_node)

        print(f"警告：无法找到从{start}到{goal}的路径")
        return []  # 没有找到路径


def test_astar():
    """测试A*算法"""
    # 创建一个简单的测试场景
    start = Position(0, 0)
    goal = Position(4, 4)
    obstacles = {Position(2, 2), Position(2, 3), Position(3, 2)}
    bounds = (0, 5)  # 6x6的网格

    # 创建A*实例并查找路径
    astar = AStar()
    path = astar.find_path(start, goal, obstacles, bounds)

    print(path)
    # 打印结果
    if path:
        print("找到路径:")
        print(" -> ".join([f"({pos.x}, {pos.y})" for pos in path]))
    else:
        print("未找到路径")


if __name__ == "__main__":
    test_astar()