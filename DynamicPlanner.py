# from WareHouse_system import Warehouse
from AStarPlanning import AStarPlanning
class DynamicPlanner:
    def __init__(self, warehouse):
        self.wHouse = warehouse


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
            task_time +=1

        return task_time / remaining_time

    def collision(self, main_robot: str, robot2: str) -> str:
        r1 = self.wHouse.robots[main_robot]
        r2 = self.wHouse.robots[robot2]

        if r2.future_route is None:
            self.wHouse.dynamic_planner._set_route(robot2)
        #后追前
        #当处于后追前时，后方机器人暂停移动一次
        if r1.future_route[1] == r2.future_route[0]:
            return "chase"
        elif r2.future_route[0] != r1.future_route[1]:
            return "blocked"

        if r2.future_route == r1.position:
            p1 = self.priority_calculator(main_robot)
            p2 = self.priority_calculator(robot2)
            if p1 > p2:
                self._set_route(robot2)
            elif p1 < p2:
                self._set_route(main_robot)
            else:
                self._set_route(main_robot)

    def stop_one_step(self, main_robot: str) -> bool:
        """
        :param main_robot:
        :return: bool
        """
        r = self.wHouse.robots[main_robot]
        r.future_route.insert(0,r.position)
        return True

    def assignment_type(self, main_robot: str,robot2:str, types: str) -> str:
        """
        当不知道使用哪种规划方法时使用此方法可自动找出应使用的动态规划方法
        :param main_robot:
        :param robot2:
        :param types:
        :return:
        """
        if types == "collision":
            return self.collision(main_robot, robot2)

    def _set_route(self, rid: str) -> bool:
        robot = self.wHouse.robots[rid]
        self.wHouse.flash_robots_position()
        robot.future_route = AStarPlanning.find_path(
            robot.position,
            robot.target,
            self.wHouse.robot_positions
        )


