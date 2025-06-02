import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from typing import Dict, List
from WareHouse_system import Robot, Warehouse

def generate_heatmap(warehouse: Warehouse, output_file: str = "warehouse_heatmap.png"):
    """
    Generate a heatmap from robot history routes
    
    Args:
        warehouse: The Warehouse instance containing robots and their history
        output_file: The output file path for the heatmap image
    """
    # Initialize the heatmap matrix with zeros
    heatmap_data = np.zeros((warehouse.height, warehouse.width))
    
    # Aggregate all robot positions from their history routes
    for robot_id, robot in warehouse.robots.items():
        for position, _ in robot.history_route:
            # Increment the count for each position visited
            heatmap_data[position.y, position.x] += 1
    
    # Create the heatmap plot
    plt.figure(figsize=(12, 8))
    sns.heatmap(heatmap_data, 
                cmap='YlOrRd',  # Yellow-Orange-Red colormap
                annot=True,     # Show numbers in cells
                fmt='.0f',      # Format numbers as integers
                cbar_kws={'label': 'Visit Count'})
    
    plt.title('Warehouse Robot Path Heatmap')
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    
    # Save the plot to file
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Heatmap has been saved to {output_file}")

if __name__ == "__main__":
    # Example usage
    warehouse = Warehouse(20, 20)
    generate_heatmap(warehouse) 