import random
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class Direction(Enum):
    UP = (0, -1)  # 向上移动时y减小
    DOWN = (0, 1)  # 向下移动时y增加
    LEFT = (-1, 0)  # 向左移动时x减小
    RIGHT = (1, 0)  # 向右移动时x增加


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


class Robot:
    def __init__(self, robot_id: str, initial_position: Position):
        self.robot_id = robot_id
        self.position = initial_position
        self.carrying_item: Optional[str] = None  # 存储正在携带的货物ID（A, B, C...）
        self.item_source: Optional[str] = None  # 存储货物来源的取货点ID（PA, PB...）

    def move(self, direction: Direction) -> Position:
        """移动机器人到新的位置"""
        self.position = self.position + direction.value
        return self.position

    def pick_item(self, item_id: str):
        """拾取物品，只存储字母部分"""
        if self.carrying_item is not None:
            return False  # 如果已经携带物品，不能拾取新物品
        if item_id.startswith('P'):
            self.carrying_item = item_id[1:]  # 将'PA'转换为'A'
            self.item_source = item_id  # 记录来源取货点
        else:
            self.carrying_item = item_id
            self.item_source = None
        return True

    def deliver_item(self):
        """交付物品，返回物品来源和物品ID。只能在支付台使用。"""
        delivered_item = self.carrying_item
        source = self.item_source
        self.carrying_item = None
        self.item_source = None
        return source, delivered_item


class Warehouse:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.robots: Dict[str, Robot] = {}
        self.delivery_station = Position(width - 1, height - 1)
        self.robot_positions = set()  # 用于跟踪机器人位置
        self.pickup_points: Dict[str, Position] = {}  # 存储所有取货点，键为取货点ID（PA, PB等）
        self.picked_shelves = set()  # 存储已被拾取的货架ID

    def _generate_next_letter_id(self) -> str:
        """生成下一个字母ID，类似Excel列名：A, B, ..., Z, AA, AB, ..., AZ, BA, BB, ..."""

        def int_to_excel_col(n: int) -> str:
            result = ""
            n = n - 1  # 转换为0-based索引
            while n >= 0:
                remainder = n % 26
                result = chr(65 + remainder) + result
                n = n // 26 - 1
            return result

        return int_to_excel_col(len(self.pickup_points) + 1)

    def add_pickup_point(self) -> Optional[str]:
        """添加一个新的取货点，返回新取货点的ID"""
        # 计算下一个取货点的字母标识
        next_letter = self._generate_next_letter_id()
        pickup_id = f"P{next_letter}"

        # 获取所有可用位置
        occupied_positions = {(pos.x, pos.y) for pos in self.pickup_points.values()}
        occupied_positions.add((self.delivery_station.x, self.delivery_station.y))
        occupied_positions.update(self.robot_positions)

        available_positions = [(x, y) for x in range(self.width) for y in range(self.height)
                               if (x, y) not in occupied_positions]

        if not available_positions:
            return None

        # 随机选择一个可用位置
        pos_x, pos_y = random.choice(available_positions)
        self.pickup_points[pickup_id] = Position(pos_x, pos_y)
        return pickup_id

    def remove_pickup_point(self, pickup_id: str) -> bool:
        """移除指定的取货点，如果取货点上有机器人则不能移除"""
        if pickup_id not in self.pickup_points:
            return False

        pickup_pos = self.pickup_points[pickup_id]
        # 检查是否有机器人在这个取货点上
        for robot in self.robots.values():
            if robot.position == pickup_pos:
                return False

        del self.pickup_points[pickup_id]
        return True

    def add_robot(self, robot_id: str, initial_position: Optional[Position] = None) -> bool:
        """添加新机器人到指定位置，如果不指定位置则放在空闲位置"""
        if robot_id in self.robots:
            return False

        if initial_position is None:
            # 找一个不是取货点也不是支付台的空闲位置
            occupied_positions = {(pos.x, pos.y) for pos in self.pickup_points.values()}
            occupied_positions.add((self.delivery_station.x, self.delivery_station.y))
            occupied_positions.update(self.robot_positions)

            available_positions = [(x, y) for x in range(self.width) for y in range(self.height)
                                   if (x, y) not in occupied_positions]

            if not available_positions:
                return False

            pos_x, pos_y = random.choice(available_positions)
            initial_position = Position(pos_x, pos_y)

        if not self._is_position_valid(initial_position) or \
                not self._is_position_available(initial_position):
            return False

        robot = Robot(robot_id, initial_position)
        self.robots[robot_id] = robot
        self.robot_positions.add((initial_position.x, initial_position.y))
        return True

    def place_robot_at_pickup(self, robot_id: str, pickup_id: str) -> bool:
        """将指定机器人放置到指定取货点，如果成功则自动拾取物品"""
        if robot_id not in self.robots or pickup_id not in self.pickup_points:
            return False

        pickup_pos = self.pickup_points[pickup_id]
        # 检查取货点是否已被占用
        if not self._is_position_available(pickup_pos):
            return False

        robot = self.robots[robot_id]
        # 移除原位置
        self.robot_positions.remove((robot.position.x, robot.position.y))
        # 更新到新位置
        robot.position = pickup_pos
        self.robot_positions.add((pickup_pos.x, pickup_pos.y))
        # 自动拾取物品
        if robot.pick_item(pickup_id):
            self.picked_shelves.add(pickup_id)  # 标记货架已被拾取
        return True

    def remove_robot(self, robot_id: str) -> bool:
        """从仓库中移除机器人"""
        if robot_id not in self.robots:
            return False

        robot = self.robots[robot_id]
        self.robot_positions.remove((robot.position.x, robot.position.y))
        del self.robots[robot_id]
        return True

    def move_robot(self, robot_id: str, direction: Direction) -> bool:
        """移动指定的机器人"""
        if robot_id not in self.robots:
            return False

        robot = self.robots[robot_id]
        new_position = robot.position + direction.value

        if not self._is_position_valid(new_position) or \
                not self._is_position_available(new_position):
            return False

        # 更新机器人位置
        self.robot_positions.remove((robot.position.x, robot.position.y))
        robot.move(direction)
        self.robot_positions.add((robot.position.x, robot.position.y))

        # 检查是否到达支付台并且携带货物
        if (robot.position.x == self.delivery_station.x and
                robot.position.y == self.delivery_station.y):
            if robot.carrying_item is not None:
                source, delivered_item = robot.deliver_item()
                print(f"机器人{robot_id}在支付台交付货物{delivered_item}")

                # 根据交付的货物ID创建对应的取货点ID
                new_pickup_id = f"P{delivered_item}"

                # 如果已存在相同ID的货架，先移除
                if new_pickup_id in self.pickup_points:
                    self.remove_pickup_point(new_pickup_id)
                    print(f"移除货架{new_pickup_id}")

                # 获取所有可用位置
                occupied_positions = {(pos.x, pos.y) for pos in self.pickup_points.values()}
                occupied_positions.add((self.delivery_station.x, self.delivery_station.y))
                occupied_positions.update(self.robot_positions)
                occupied_positions.remove((robot.position.x, robot.position.y))

                available_positions = [(x, y) for x in range(self.width) for y in range(self.height)
                                       if (x, y) not in occupied_positions]

                if available_positions:
                    # 随机选择一个可用位置，创建新货架
                    pos_x, pos_y = random.choice(available_positions)
                    self.pickup_points[new_pickup_id] = Position(pos_x, pos_y)
                    print(f"创建新货架{new_pickup_id}")
                    # 新创建的货架未被拾取
                    if new_pickup_id in self.picked_shelves:
                        self.picked_shelves.remove(new_pickup_id)
                else:
                    print("无法创建新货架，仓库已满")

        # 检查机器人是否在某个取货点上
        if robot.carrying_item is None:  # 只有未携带物品的机器人才能拾取
            for pickup_id, pickup_pos in self.pickup_points.items():
                if (robot.position.x == pickup_pos.x and
                        robot.position.y == pickup_pos.y and
                        pickup_id not in self.picked_shelves):  # 只能拾取未被拾取过的货架
                    robot.pick_item(pickup_id)
                    self.picked_shelves.add(pickup_id)  # 标记货架已被拾取
                    print(f"机器人{robot_id}拾取货架{pickup_id}的物品")
                    break

        return True

    def _is_position_valid(self, position: Position) -> bool:
        """检查位置是否在仓库范围内"""
        return (0 <= position.x < self.width and
                0 <= position.y < self.height)

    def _is_position_available(self, position: Position) -> bool:
        """检查位置是否被其他机器人占用"""
        return (position.x, position.y) not in self.robot_positions

    def display_warehouse(self):
        """以表格形式显示仓库状态"""
        # 创建表头，确保每个数字占据8个字符的宽度并居中对齐
        header = "      " + "".join(f"{i:^8}" for i in range(self.width))
        print(header)
        print("     +" + "--------" * self.width + "+")

        # 创建仓库地图
        for y in range(self.height):
            row = f"{y:2}   |"
            for x in range(self.width):
                current_pos = Position(x, y)
                cell_content = "   .    "  # 默认为空格子，8个字符宽度

                # 检查是否有机器人
                robot_found = False
                for robot_id, robot in self.robots.items():
                    if robot.position.x == x and robot.position.y == y:
                        # 检查机器人是否在支付台位置
                        if x == self.delivery_station.x and y == self.delivery_station.y:
                            cell_content = f"{robot_id}/D".center(8)
                        else:
                            # 检查机器人是否在取货点位置
                            shelf_at_position = None
                            for pickup_id, pickup_pos in self.pickup_points.items():
                                if pickup_pos.x == x and pickup_pos.y == y:
                                    shelf_at_position = pickup_id
                                    break

                            # 根据不同情况显示机器人状态
                            if robot.carrying_item is not None:
                                if shelf_at_position:
                                    # 携带物品的机器人在货架位置
                                    cell_content = f"{robot_id}/{robot.carrying_item}/{shelf_at_position}".center(8)
                                else:
                                    # 携带物品的机器人在普通位置
                                    cell_content = f"{robot_id}/{robot.carrying_item}".center(8)
                            else:
                                if shelf_at_position:
                                    # 未携带物品的机器人在货架位置
                                    cell_content = f"{robot_id}/{shelf_at_position}".center(8)
                                else:
                                    # 未携带物品的机器人在普通位置
                                    cell_content = f"{robot_id}".center(8)

                        robot_found = True
                        break

                # 如果没有机器人，检查其他元素
                if not robot_found:
                    # 检查是否是支付台
                    if x == self.delivery_station.x and y == self.delivery_station.y:
                        cell_content = "   D    "
                    # 检查是否是取货点 - 始终显示取货点
                    else:
                        for pickup_id, pos in self.pickup_points.items():
                            if pos.x == x and pos.y == y:
                                # 添加标识显示货架是否已被拾取
                                picked = '*' if pickup_id in self.picked_shelves else ''
                                cell_content = f"{pickup_id}{picked}".center(8)
                                break

                row += cell_content
            row += "|"
            print(row)

        # 打印底部边框
        print("     +" + "--------" * self.width + "+")
        print("\n图例: .  = 空格子, D = 支付台")
        print("     PA* = 已被拾取的货架, PA = 未被拾取的货架")
        print("     R1/A = 机器人R1携带A货物")
        print("     R1/A/PB = 机器人R1携带A货物且位于PB货架位置")
        print("     R1/D = 机器人R1在支付台")

    def add_robot_with_pickup(self, robot_id: str) -> Tuple[bool, Optional[str]]:
        """创建机器人并自动为其分配新的取货点

        Returns:
            Tuple[bool, Optional[str]]: (是否成功, 分配的取货点ID)
        """
        # 先创建新的取货点
        pickup_id = self.add_pickup_point()
        if not pickup_id:
            print(f"无法为机器人{robot_id}创建新的取货点")
            return False, None

        # 先在一个临时位置创建机器人
        temp_pos = None
        for x in range(self.width):
            for y in range(self.height):
                pos = Position(x, y)
                if self._is_position_valid(pos) and self._is_position_available(pos):
                    temp_pos = pos
                    break
            if temp_pos:
                break

        if not temp_pos:
            self.remove_pickup_point(pickup_id)
            return False, None

        # 创建机器人在临时位置
        if not self.add_robot(robot_id, temp_pos):
            self.remove_pickup_point(pickup_id)
            return False, None

        # 将机器人移动到取货点并拾取物品
        if not self.place_robot_at_pickup(robot_id, pickup_id):
            self.remove_robot(robot_id)
            self.remove_pickup_point(pickup_id)
            return False, None

        print(f"机器人{robot_id}已创建并分配到取货点{pickup_id}")
        return True, pickup_id


def main():
    # 创建一个6x6的仓库示例
    warehouse = Warehouse(6, 6)

    # 添加机器人R1
    print("\n创建机器人R1:")
    success, pickup_id = warehouse.add_robot_with_pickup("R1")
    if success:
        print(f"机器人R1已分配到取货点{pickup_id}")
        print(f"机器人R1携带物品: {warehouse.robots['R1'].carrying_item}")
        print(f"物品来源: {warehouse.robots['R1'].item_source}")
    warehouse.display_warehouse()

    # 添加机器人R2
    print("\n创建机器人R2:")
    success, pickup_id = warehouse.add_robot_with_pickup("R2")
    if success:
        print(f"机器人R2已分配到取货点{pickup_id}")
        print(f"机器人R2携带物品: {warehouse.robots['R2'].carrying_item}")
        print(f"物品来源: {warehouse.robots['R2'].item_source}")
    warehouse.display_warehouse()

    # R1的运动路径：向右到底 -> 向下到底 -> 交付 -> 向上到顶
    print("\n机器人R1开始移动:")
    print("R1向右移动到底:")
    for _ in range(warehouse.width):  # 向右移动
        if warehouse.move_robot("R1", Direction.RIGHT):
            print(f"机器人R1携带物品: {warehouse.robots['R1'].carrying_item}")
            warehouse.display_warehouse()

    print("\nR1向下移动到底:")
    for _ in range(warehouse.height):  # 向下移动
        if warehouse.move_robot("R1", Direction.DOWN):
            print(f"机器人R1携带物品: {warehouse.robots['R1'].carrying_item}")
            warehouse.display_warehouse()

    print("\nR1向上移动到顶:")
    for _ in range(warehouse.height):  # 向上移动
        if warehouse.move_robot("R1", Direction.UP):
            print(f"机器人R1携带物品: {warehouse.robots['R1'].carrying_item}")
            warehouse.display_warehouse()

    # R2的运动路径：向下到底 -> 向右到底 -> 交付 -> 向左到头
    print("\n机器人R2开始移动:")
    print("R2向下移动到底:")
    for _ in range(warehouse.height):  # 向下移动
        if warehouse.move_robot("R2", Direction.DOWN):
            print(f"机器人R2携带物品: {warehouse.robots['R2'].carrying_item}")
            warehouse.display_warehouse()

    print("\nR2向右移动到底:")
    for _ in range(warehouse.width):  # 向右移动
        if warehouse.move_robot("R2", Direction.RIGHT):
            print(f"机器人R2携带物品: {warehouse.robots['R2'].carrying_item}")
            warehouse.display_warehouse()

    print("\nR2向左移动到头:")
    for _ in range(warehouse.width):  # 向左移动
        if warehouse.move_robot("R2", Direction.LEFT):
            print(f"机器人R2携带物品: {warehouse.robots['R2'].carrying_item}")
            warehouse.display_warehouse()


if __name__ == "__main__":
    main()