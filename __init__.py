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
    print("we")
    success, pickup_id = warehouse.add_robot_with_pickup("R1")
    success, pickup_id = warehouse.add_robot_with_pickup("R2")
    success, pickup_id = warehouse.add_robot_with_pickup("R3")
    success, pickup_id = warehouse.add_robot_with_pickup("R4")
    success, pickup_id = warehouse.add_robot_with_pickup("R5")

    warehouse.display_warehouse()
    while True:
        warehouse.tick()
        warehouse.display_warehouse()


def func3():
    print(Direction.get_directions())

func2()
#func3()





