import pandas as pd
import open3d as o3d
import numpy as np

import matplotlib.pyplot as plt

# Read the CSV file
file_path = 'combine0715.csv'  # here use the output file from combination_to_CSV.py as an example
data = pd.read_csv(file_path)

target_image = '2024-07-15_11-49-30-021134.png'

filtered_df = data[data['ID'] == target_image]

print(filtered_df)
# Extract point cloud data
points = filtered_df[['X', 'Y', 'Z']].values
intensity = filtered_df['Intensity'].values

# Create an open3d point cloud object
pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(points)


# Create a color map, assuming the range of Intensity is [0, 1]
intensity_normalized = (intensity - intensity.min()) / (intensity.max() - intensity.min())
colors = plt.cm.viridis(intensity_normalized)[:, :3]  # Use viridis colormap

pcd.colors = o3d.utility.Vector3dVector(colors)

# Visualize the point cloud
o3d.visualization.draw_geometries([pcd], window_name='3D Point Cloud Visualization', width=800, height=600)
