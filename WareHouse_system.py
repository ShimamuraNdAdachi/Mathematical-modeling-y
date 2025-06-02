import random
import time
from datetime import time as dt_time
from typing import List, Tuple, Dict, Optional
from Direction import Direction
from Position import Position
from DynamicPlanner import DynamicPlanner
from AStarPlanning import AStarPlanning

class Robot:
    def __init__(self, robot_id: str, initial_position: Position):
        self.robot_id = robot_id
        self.position = initial_position
        self.carrying_item: Optional[str] = None  # 存储正在携带的货物ID（A, B, C...）
        self.item_source: Optional[str] = None  # 存储货物来源的取货点ID（PA, PB...）
        self.future_route: List[Position] = []  #存储机器人未来的路线
        self.history_route: List[tuple] = []
        self.target: Position = None

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

class Goods:
    def __init__(self, goods_id: str, initial_position: Position):
        self.id = goods_id
        self.pos = initial_position

class Warehouse:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.robots: Dict[str, Robot] = {}
        self.delivery_station = Position(width - 1, height - 1)
        self.robot_positions = set() # 用于跟踪机器人位置的缓存
        self.pickup_points: Dict[str, Position] = {}  # 存储所有取货点，键为取货点ID（PA, PB等）
        self.picked_shelves = set()  # 存储已被拾取的货架ID
        self.tick_count: int = 0
        self.dynamic_planner: DynamicPlanner = DynamicPlanner(self)
        self.tick_successMoveCount: int = 0
        self.unpicked_positions = []
        self.completed_tasks = 0  # 完成的任务数量

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

        # 获取所有已占用的位置
        occupied_positions = {(pos.x, pos.y) for pos in self.pickup_points.values()}
        occupied_positions.add((self.delivery_station.x, self.delivery_station.y))
        self.flash_robots_position()
        occupied_positions.update(self.robot_positions)

        # 获取所有可用位置
        available_positions = []
        for x in range(self.width):
            for y in range(self.height):
                if (x, y) not in occupied_positions:
                    # 确保不会在支付台的紧邻位置创建取货点
                    if abs(x - self.delivery_station.x) + abs(y - self.delivery_station.y) > 1:
                        available_positions.append((x, y))

        if not available_positions:
            print(f"无法创建取货点{pickup_id}：没有可用位置")
            return None

        # 随机选择一个位置
        pos_x, pos_y = random.choice(available_positions)
        self.pickup_points[pickup_id] = Position(pos_x, pos_y)
        print(f"创建取货点{pickup_id}在位置({pos_x}, {pos_y})")
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
            self.flash_robots_position()
            occupied_positions.update(self.robot_positions)

            available_positions = [(x, y) for x in range(self.width) for y in range(self.height)
                                if (x, y) not in occupied_positions]

            if not available_positions:
                return False

            pos_x, pos_y = random.choice(available_positions)
            initial_position = Position(pos_x, pos_y)
        elif not self._is_position_valid(initial_position):
            print(f"位置 ({initial_position.x}, {initial_position.y}) 超出仓库范围")
            return False
        elif not self._is_position_available(initial_position):
            print(f"位置 ({initial_position.x}, {initial_position.y}) 已被占用")
            return False

        robot = Robot(robot_id, initial_position)
        robot.target = self.delivery_station
        self.robots[robot_id] = robot
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
        #self.robot_positions.remove((robot.position.x, robot.position.y))
        # 更新到新位置
        robot.position = pickup_pos
        #self.robot_positions.add((pickup_pos.x, pickup_pos.y))
        # 自动拾取物品
        if robot.pick_item(pickup_id):
            self.picked_shelves.add(pickup_id)  # 标记货架已被拾取
        return True

    def remove_robot(self, robot_id: str) -> bool:
        """从仓库中移除机器人"""
        if robot_id not in self.robots:
            return False

        robot = self.robots[robot_id]
        #self.robot_positions.remove((robot.position.x, robot.position.y))
        del self.robots[robot_id]
        return True

    def on_pickup(self, rid: str):
        robot = self.robots[rid]
        # 检查机器人是否在某个取货点上
        if robot.carrying_item is None:  # 只有未携带物品的机器人才能拾取
            for pickup_id, pickup_pos in self.pickup_points.items():
                if (robot.position.x == pickup_pos.x and
                        robot.position.y == pickup_pos.y and
                        pickup_id not in self.picked_shelves):  # 只能拾取未被拾取过的货架
                    if robot.pick_item(pickup_id):
                        self.picked_shelves.add(pickup_id)  # 标记货架已被拾取
                        print(f"机器人{rid}成功拾取货架{pickup_id}的物品")
                        robot.target = self.delivery_station  # 设置目标为支付台
                        robot.future_route = []  # 清空路径，强制重新规划
                        print(f"机器人{rid}设置新目标：支付台")
                    else:
                        print(f"机器人{rid}无法拾取货架{pickup_id}的物品")
                    break

    def on_delivery(self, rid: str):
        """
        处理机器人到达支付台的逻辑
        - 如果机器人携带物品，则交付物品
        - 交付后创建新的取货点
        - 设置机器人的新目标
        """
        robot = self.robots[rid]
        if (robot.position.x == self.delivery_station.x and
                robot.position.y == self.delivery_station.y):
            if robot.carrying_item is not None:
                source, delivered_item = robot.deliver_item()
                print(f"机器人{rid}在支付台交付货物{delivered_item}")

                # 创建新的取货点
                attempts = 3  # 尝试创建取货点的次数
                new_pickup_id = None
                while attempts > 0:
                    new_pickup_id = self.add_pickup_point()
                    if new_pickup_id:
                        print(f"成功创建新货架{new_pickup_id}")
                        break
                    attempts -= 1
                    if attempts > 0:
                        print(f"创建取货点失败，还剩{attempts}次尝试")
                
                if not new_pickup_id:
                    print(f"机器人{rid}：无法创建新的取货点，仓库可能已满")
                    # 让机器人移动到随机位置
                    available_positions = []
                    for x in range(self.width):
                        for y in range(self.height):
                            if (x, y) not in self.robot_positions and \
                               (x, y) != (self.delivery_station.x, self.delivery_station.y):
                                available_positions.append((x, y))
                    
                    if available_positions:
                        x, y = random.choice(available_positions)
                        robot.target = Position(x, y)
                        robot.future_route = []
                        print(f"机器人{rid}移动到随机位置({x}, {y})")
                    return
                
                # 立即寻找新的未被拾取的货架作为目标
                unpicked_shelves = []
                for pickId, pickPos in self.pickup_points.items():
                    if pickId not in self.picked_shelves:
                        unpicked_shelves.append((pickId, pickPos))
                
                if unpicked_shelves:
                    # 随机选择一个未拾取的货架
                    unpicked_id, unpicked_pos = random.choice(unpicked_shelves)
                    robot.target = unpicked_pos
                    robot.future_route = []  # 清空当前路径，强制重新规划
                    print(f"机器人{rid}的新目标设置为取货点{unpicked_id}")
                else:
                    # 如果没有可用的取货点，让机器人移动到随机位置
                    available_positions = []
                    for x in range(self.width):
                        for y in range(self.height):
                            if (x, y) not in self.robot_positions and \
                               (x, y) != (self.delivery_station.x, self.delivery_station.y):
                                available_positions.append((x, y))
                    
                    if available_positions:
                        x, y = random.choice(available_positions)
                        robot.target = Position(x, y)
                        robot.future_route = []  # 清空当前路径，强制重新规划
                        print(f"机器人{rid}暂无可用取货点，移动到随机位置({x}, {y})")

    def move_robot(self, robot_id: str, direction: Direction) -> bool:
        """移动指定的机器人"""
        if robot_id not in self.robots:
            return False

        robot = self.robots[robot_id]
        new_position = robot.position + direction.value

        if not self._is_position_valid(new_position):
            return False

        if not self._is_position_available(new_position):
            self.dynamic_planner.assignment_type(
                robot_id,
                self._get_position_unavailable_robot(new_position),
                "collision"
            )
            return False

        # 更新机器人位置
        robot.move(direction)
        #self.robot_positions.remove((robot.position.x, robot.position.y))
        #self.robot_positions.add((robot.position.x, robot.position.y))



        return True

    def _is_position_valid(self, position: Position) -> bool:
        """检查位置是否在仓库范围内"""
        return (0 <= position.x < self.width and
                0 <= position.y < self.height)

    def _is_position_available(self, position: Position) -> bool:
        """检查位置是否被其他机器人占用"""
        self.flash_robots_position()
        return (position.x, position.y) not in self.robot_positions

    def _get_position_unavailable_robot(self, pos: Position) -> str:
        """
        若位置不可用，则获取该位置机器人
        :param pos:
        :return:
        """
        #空位置无法获取机器人位置
        if self._is_position_available(pos):
            return None
        #仓库边缘无机器人
        if not self._is_position_valid(pos):
            return None
        #_is_position_available已刷新robot_positions成员变量，此处无需再刷新
        for rid,r in self.robots.items():
            if r.position == pos:
                return rid

    def display_warehouse(self):
        """以表格形式显示仓库状态，使用终端刷新方式"""
        import os
        import platform

        # 清屏
        if platform.system() == "Windows":
            os.system('cls')
        else:
            os.system('clear')

        # 移动光标到终端顶部
        print("\033[H", end="")

        # 创建表头，确保每个数字占据8个字符的宽度并居中对齐
        header = "     " + "".join(f"{i:^8}" for i in range(self.width))
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
                        cell_content = "   D1   "
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
        print(f"\n当前tick数: {self.tick_count}")
        print(f"成功移动次数: {self.tick_successMoveCount}")

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

        # 获取取货点位置
        pickup_pos = self.pickup_points[pickup_id]
        
        # 创建机器人在取货点位置
        if not self.add_robot(robot_id, pickup_pos):
            self.remove_pickup_point(pickup_id)
            print(f"无法在取货点{pickup_id}创建机器人{robot_id}")
            return False, None

        # 让机器人拾取物品
        robot = self.robots[robot_id]
        if robot.pick_item(pickup_id):
            self.picked_shelves.add(pickup_id)  # 标记货架已被拾取
            robot.target = self.delivery_station  # 设置目标为支付台
            print(f"机器人{robot_id}已创建并在取货点{pickup_id}拾取物品")
            return True, pickup_id
        else:
            self.remove_robot(robot_id)
            self.remove_pickup_point(pickup_id)
            print(f"机器人{robot_id}无法在取货点{pickup_id}拾取物品")
            return False, None

    def flash_robots_position(self):
        self.robot_positions = set()
        for r_id, r in self.robots.items():
            self.robot_positions.add((r.position.x,r.position.y))

    def move_robot_use_route_plan(self, rid: str):
        """
        自动：分配路径规划；记录历史路径
        :param rid:
        :return:
        """
        robot = self.robots[rid]
        self.recorder(rid)

        # 先处理交付和拾取
        self.on_delivery(rid)
        self.on_pickup(rid)

        # 如果没有规划好的路径，需要规划新路径
        if not robot.future_route:
            # 如果携带物品，目标应该是支付台
            if robot.carrying_item is not None:
                if robot.target != self.delivery_station:
                    robot.target = self.delivery_station
                    print(f"机器人{rid}携带物品{robot.carrying_item}，前往支付台")
                if not self.dynamic_planner.set_route(rid):
                    print(f"机器人{rid}无法找到路径到支付台，等待下一次尝试")
                    return False
            else:
                # 如果没有携带物品，随机选择一个未被拾取的货架
                unpicked_shelves = []
                for pickId, pickPos in self.pickup_points.items():
                    if pickId not in self.picked_shelves:
                        unpicked_shelves.append((pickId, pickPos))
                
                if unpicked_shelves:
                    # 随机选择一个未拾取的货架
                    unpicked_id, unpicked_pos = random.choice(unpicked_shelves)
                    if robot.target != unpicked_pos:
                        robot.target = unpicked_pos
                        print(f"机器人{rid}前往取货点{unpicked_id}")
                    if not self.dynamic_planner.set_route(rid):
                        print(f"机器人{rid}无法找到路径到取货点{unpicked_id}，等待下一次尝试")
                        return False
                else:
                    # 如果没有未被拾取的货架，移动到随机位置
                    available_positions = []
                    for x in range(self.width):
                        for y in range(self.height):
                            if (x, y) not in self.robot_positions and \
                               (x, y) != (self.delivery_station.x, self.delivery_station.y):
                                available_positions.append((x, y))
                    
                    if available_positions:
                        x, y = random.choice(available_positions)
                        robot.target = Position(x, y)
                        robot.future_route = []  # 清空当前路径，强制重新规划
                        print(f"机器人{rid}暂无可用取货点，移动到随机位置({x}, {y})")
                        if not self.dynamic_planner.set_route(rid):
                            print(f"机器人{rid}无法找到路径到随机位置，等待下一次尝试")
                            return False
                    else:
                        print(f"机器人{rid}无法找到可用的移动位置")
                        return False

        # 确保有可用的路径
        if not robot.future_route:
            return False

        # 移动机器人
        if self.move_robot(rid,
                        Direction.coordinates_to_direction(
                            robot.future_route[0].x - robot.position.x,
                            robot.future_route[0].y - robot.position.y
                        )):
            robot.future_route.pop(0)
            self.tick_successMoveCount += 1
            return True

        return False

    def recorder(self, rid: str):
        """
        #记录历史路径，便于统计
        :param rid:
        :return:
        """
        r = self.robots[rid]
        for pickId, pickPoint in self.pickup_points.items():
            if pickPoint == r.position:
                r.history_route.append(
                    (r.position, 1)
                )
            elif r.position == self.delivery_station:
                r.history_route.append(
                    (r.position, 2)
                )
            else:
                r.history_route.append(
                    (r.position, 0)
                )

    def moveAll(self):
        for rid, r in self.robots.items():
            self.move_robot_use_route_plan(rid)

    def tick_time(self,times: int):
        for i in range[1:times + 1:1]:
            self.tick()

    def calculate_statistics(self):
        """计算所有机器人的统计信息"""
        total_tasks = 0
        total_task_time = 0
        total_path_length = 0
        
        for rid, robot in self.robots.items():
            # 分析历史路径
            current_task_time = 0
            current_path_length = 0
            task_count = 0
            in_task = False
            
            for i, (pos, status) in enumerate(robot.history_route):
                if status == 1:  # 在取货点
                    if not in_task:
                        in_task = True
                        current_task_time = 0
                        current_path_length = 0
                elif status == 2:  # 在支付台
                    if in_task:
                        task_count += 1
                        total_task_time += current_task_time
                        total_path_length += current_path_length
                        in_task = False
                
                if in_task:
                    current_task_time += 1
                    if i > 0:
                        prev_pos = robot.history_route[i-1][0]
                        current_path_length += abs(pos.x - prev_pos.x) + abs(pos.y - prev_pos.y)
            
            print(f"\n机器人{rid}统计信息:")
            print(f"完成任务数: {task_count}")
            if task_count > 0:
                print(f"平均任务时间: {current_task_time/task_count:.2f} ticks")
                print(f"平均路径长度: {current_path_length/task_count:.2f} 格")
            
            total_tasks += task_count
        
        print("\n整体统计信息:")
        print(f"总任务数: {total_tasks}")
        if total_tasks > 0:
            print(f"平均任务时间: {total_task_time/total_tasks:.2f} ticks")
            print(f"平均路径长度: {total_path_length/total_tasks:.2f} 格")
            print(f"每个tick的平均移动成功率: {(self.tick_successMoveCount/self.tick_count/len(self.robots))*100:.2f}%")

    def tick(self) -> int:
        """
        所有机器人根据路径列表全部进行一次移动
        :return: tuple(每次tick所消耗时间，单位毫秒ms;成功移动总次数)
        """
        start_time = time.perf_counter()

        self.moveAll()
        self.dynamic_planner.check()
        self.tick_count += 1

        # 每100个tick显示一次统计信息
        if self.tick_count % 100 == 0:
            self.calculate_statistics()

        end_time = time.perf_counter()
        return (end_time - start_time) * 1000


def main():
    print("w")
    # # 创建一个6x6的仓库示例
    # warehouse = Warehouse(6, 6)
    #
    # # 添加机器人R1
    # print("\n创建机器人R1:")
    # success, pickup_id = warehouse.add_robot_with_pickup("R1")
    # if success:
    #     print(f"机器人R1已分配到取货点{pickup_id}")
    #     print(f"机器人R1携带物品: {warehouse.robots['R1'].carrying_item}")
    #     print(f"物品来源: {warehouse.robots['R1'].item_source}")
    # warehouse.display_warehouse()
    #
    # # 添加机器人R2
    # print("\n创建机器人R2:")
    # success, pickup_id = warehouse.add_robot_with_pickup("R2")
    # if success:
    #     print(f"机器人R2已分配到取货点{pickup_id}")
    #     print(f"机器人R2携带物品: {warehouse.robots['R2'].carrying_item}")
    #     print(f"物品来源: {warehouse.robots['R2'].item_source}")
    # warehouse.display_warehouse()
    #
    # # R1的运动路径：向右到底 -> 向下到底 -> 交付 -> 向上到顶
    # print("\n机器人R1开始移动:")
    # print("R1向右移动到底:")
    # for _ in range(warehouse.width):  # 向右移动
    #     if warehouse.move_robot("R1", Direction.RIGHT):
    #         print(f"机器人R1携带物品: {warehouse.robots['R1'].carrying_item}")
    #         warehouse.display_warehouse()
    #
    # print("\nR1向下移动到底:")
    # for _ in range(warehouse.height):  # 向下移动
    #     if warehouse.move_robot("R1", Direction.DOWN):
    #         print(f"机器人R1携带物品: {warehouse.robots['R1'].carrying_item}")
    #         warehouse.display_warehouse()
    #
    # print("\nR1向上移动到顶:")
    # for _ in range(warehouse.height):  # 向上移动
    #     if warehouse.move_robot("R1", Direction.UP):
    #         print(f"机器人R1携带物品: {warehouse.robots['R1'].carrying_item}")
    #         warehouse.display_warehouse()
    #
    # # R2的运动路径：向下到底 -> 向右到底 -> 交付 -> 向左到头
    # print("\n机器人R2开始移动:")
    # print("R2向下移动到底:")
    # for _ in range(warehouse.height):  # 向下移动
    #     if warehouse.move_robot("R2", Direction.DOWN):
    #         print(f"机器人R2携带物品: {warehouse.robots['R2'].carrying_item}")
    #         warehouse.display_warehouse()
    #
    # print("\nR2向右移动到底:")
    # for _ in range(warehouse.width):  # 向右移动
    #     if warehouse.move_robot("R2", Direction.RIGHT):
    #         print(f"机器人R2携带物品: {warehouse.robots['R2'].carrying_item}")
    #         warehouse.display_warehouse()
    #
    # print("\nR2向左移动到头:")
    # for _ in range(warehouse.width):  # 向左移动
    #     if warehouse.move_robot("R2", Direction.LEFT):
    #         print(f"机器人R2携带物品: {warehouse.robots['R2'].carrying_item}")
    #         warehouse.display_warehouse()


if __name__ == "__main__":
    main()
