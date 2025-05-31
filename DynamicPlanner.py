# from WareHouse_system import Warehouse
from math import sqrt
from time import sleep
from AStar import AStar
from AStarPlanning import AStarPlanning
from Position import Position


class DynamicPlanner:
    def __init__(self, warehouse):
        self.wHouse = warehouse
        self.all_robot_count = len(self.wHouse.robots)
        """
        检查收货地周围延迟公式：
        检测延迟与边长成正比，与机器人数量成反比
        单位为机器人移动次数
        """
        self.check_close_toDelivery_delay = 1

        """
        此处公式结果应与机器人数量与长，宽成正比
        单位为格数
        """
        self.close_toDelivery_width = int(self.wHouse.width / 10) + 1
        self.close_toDelivery_height = int(self.wHouse.height / 10) + 1


    def priority_calculator(self, r: str) -> float:
        """
        Priority(Ri)= 已执行任务时间/剩余任务时间
        :param r:
        :return:
        """
        robot = self.wHouse.robots[r]
        task_time = 0
        remaining_time = len(robot.future_route)
        for pos, status in reversed(robot.history_route):
            if status:
                break
            task_time += 1

        return task_time / remaining_time

    def check_close_toDelivery(self) -> int:
        wH = self.wHouse
        close_toDelivery_count = 0

        wH.flash_robots_position()
        for rx, ry in wH.robot_positions:
            if (wH.width - self.close_toDelivery_width <= rx <= wH.width - 1 and
                    wH.height - self.close_toDelivery_height <= ry <= wH.height - 1):
                close_toDelivery_count += 1
        # rx = wH.width - check_width
        # ry = wH.height - check_height
        # while rx <= wH.width - 1:
        #     while ry <= wH.height - 1:
        return close_toDelivery_count

    def check(self):
        if self.wHouse.tick_count % self.check_close_toDelivery_delay == 0:
            if self.check_close_toDelivery() >= int(sqrt(self.close_toDelivery_width * self.close_toDelivery_height)):
                self.assignment_type(None, None, "overcrowded_at_delivery")

    def collision(self, main_robot: str, robot2: str) -> str:
        r1 = self.wHouse.robots[main_robot]
        r2 = self.wHouse.robots[robot2]

        if not r2.future_route:
            self.wHouse.dynamic_planner.set_route(robot2)
        #后追前
        #当处于后追前时，后方机器人暂停移动一次
        if len(r1.future_route) == 1:
            return "approaching_delivery"
        if len(r1.future_route) < 2 and len(r2.future_route) < 2:
            return "route_wrong"
        if r1.future_route[1] == r2.future_route[0]:
            return "chase"
        elif r2.future_route[0] != r1.future_route[1] and r2.future_route[0] != r1.position:
            return "blocked"

        if r2.future_route[0] == r1.position:
            p1 = self.priority_calculator(main_robot)
            p2 = self.priority_calculator(robot2)
            if p1 > p2:
                self.set_route(robot2)
            elif p1 < p2:
                self.set_route(main_robot)
            else:
                self.set_route(main_robot)

    def stop_one_step(self, main_robot: str) -> bool:
        """
        :param main_robot:
        :return: bool
        """
        r = self.wHouse.robots[main_robot]
        r.future_route.insert(0,r.position)
        return True

    def assignment_type(self, main_robot: str, robot2: str, types: str) -> str:
        """
        当不知道使用哪种规划方法时使用此方法可自动找出应使用的动态规划方法
        :param main_robot:
        :param robot2:
        :param types:
        :return:
        """
        if types == "collision":
            return self.collision(main_robot, robot2)
        if types == "overcrowded_at_delivery":
            return self.solve_overcrowded_at_delivery()

    def solve_overcrowded_at_delivery(self) -> str:
       pass
    def set_route(self, rid: str) -> bool:
        robot = self.wHouse.robots[rid]


        # if robot.carrying_item is not None:
        #     robot.target = self.wHouse.delivery_station
        # else:
        #     for pickId, pickPos in self.wHouse.pickup_points:
        #         if (robot.target == pickPos
        #                 # 检查当前目标取货点是否被其他机器人拾取
        #                 and pickId in self.wHouse.picked_shelves
        #                 and not robot.position == pickPos):
        #             # 返回距离当前位置最近的未被拾取的取货点位置
        #             unpicked_positions = [
        #                 (pickup_id, position)
        #                 for pickup_id, position in self.wHouse.pickup_points.items()
        #                 if pickup_id not in self.wHouse.pickup_points
        #             ]
        #
        #             # if not unpicked_positions:
        #
        #             # 计算距离并排序（假设 Position 有 x, y 属性）
        #             nearest = min(
        #                 unpicked_positions,
        #                 key=lambda item: ((item[1].x - robot.position.x) ** 2 +
        #                                   (item[1].y - robot.position.y) ** 2) ** 0.5
        #             )
        #             robot.target = nearest[1]
        #             print(robot.target)


        # 使用仓库的宽度和高度作为边界
        # allRobotPositions = set()
        # for rids, r in self.wHouse.robots:
        #     allRobotPositions.add(r.position)
        self.wHouse.flash_robots_position()
        bounds = (0, min(self.wHouse.width - 1, self.wHouse.height - 1))
        astar = AStar()
        obstacles = {Position(x, y) for x, y in self.wHouse.robot_positions}
        obstacles.discard(robot.position)
        obstacles.discard(self.wHouse.delivery_station)

        robot.future_route = astar.find_path(
            robot.position,
            robot.target,
            obstacles,
            bounds
        )
        # robot.future_route = AStarPlanning.find_path(
        #     robot.position,
        #     robot.target,
        #     self.wHouse.robot_positions,
        #     bounds
        # )
        if True:
            print("\n\neeeeeeeeeeeeeeeeeeeeeeeeeeee")
            print(f"rid:{robot.robot_id}")
            print(f"rPos:{robot.position}")
            print(f"rTgt:{robot.target}")
            print(f"allRobotPos:{self.wHouse.robot_positions}")
            print(f"zhangaiwu:{obstacles}")
            print(f"unpickPos:{self.wHouse.unpicked_positions}")
            print(f"picked_she{self.wHouse.picked_shelves}")
            print(f"bounds:{bounds}")
            print(f"futureRoute:{robot.future_route}")
            print("eeeeeeeeeeeeeeeeeeeeeeeeeeee\n\n")

        if not robot.future_route:
            return False
        return True



