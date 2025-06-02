from time import sleep

from WareHouse_system import Robot
from WareHouse_system import Warehouse
from Direction import Direction

def func1():
    warehouse = Warehouse(6, 6)

    print("\n创建机器人R1:")
    success, pickup_id = warehouse.add_robot_with_pickup("R1")
    if success:
        print(f"机器人R1已分配到取货点{pickup_id}")
        print(f"机器人R1携带物品: {warehouse.robots['R1'].carrying_item}")
        print(f"物品来源: {warehouse.robots['R1'].item_source}")
    warehouse.display_warehouse()

    print("\n创建机器人R2:")
    success, pickup_id = warehouse.add_robot_with_pickup("R2")
    if success:
        print(f"机器人R2已分配到取货点{pickup_id}")
        print(f"机器人R2携带物品: {warehouse.robots['R2'].carrying_item}")
        print(f"物品来源: {warehouse.robots['R2'].item_source}")
    warehouse.display_warehouse()

def func2():
    warehouse = Warehouse(20, 20)
    print("初始化仓库系统...")
    success, pickup_id = warehouse.add_robot_with_pickup("R1")
    success, pickup_id = warehouse.add_robot_with_pickup("R2")
    success, pickup_id = warehouse.add_robot_with_pickup("R3")
    success, pickup_id = warehouse.add_robot_with_pickup("R4")
    success, pickup_id = warehouse.add_robot_with_pickup("R5")

    warehouse.display_warehouse()
    max_ticks = 1000  # 最大运行1000个时间单位
    tick_count = 0
    
    try:
        while tick_count < max_ticks:
            # 显示当前状态
            print("\n当前状态:")
            print("取货点:", warehouse.pickup_points)
            print("已拾取货架:", warehouse.picked_shelves)
            for rid, robot in warehouse.robots.items():
                print(f"机器人{rid}: 位置={robot.position}, 携带={robot.carrying_item}, 目标={robot.target}")
            
            warehouse.tick()
            warehouse.display_warehouse()
            sleep(0.5)  # 添加0.5秒延时，使显示更容易观察
            tick_count += 1
            
            # 检查是否所有机器人都完成了任务
            all_done = True
            for rid, robot in warehouse.robots.items():
                if robot.carrying_item is not None or len(robot.future_route) > 0:
                    all_done = False
                    break
            
            if all_done and False:
                print("\n所有机器人已完成任务！")
                break
                
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    finally:
        print("\n=== 最终统计信息 ===")
        warehouse.calculate_statistics()


def func3():
    print(Direction.get_directions())
    warehouse = Warehouse(20, 20)
    print("we")
    success, pickup_id = warehouse.add_robot_with_pickup("R1")
    success, pickup_id = warehouse.add_robot_with_pickup("R2")
    success, pickup_id = warehouse.add_robot_with_pickup("R3")
    success, pickup_id = warehouse.add_robot_with_pickup("R4")
    success, pickup_id = warehouse.add_robot_with_pickup("R5")

    warehouse.display_warehouse()
    for rid, r in warehouse.robots.items():
        print(r.position)
    print("\n\n\n\n\n")
    # warehouse.flash_robots_position()
    print(warehouse.robot_positions)

func2()






