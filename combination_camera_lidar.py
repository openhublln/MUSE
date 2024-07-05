# Import necessary libraries
import os
import pandas as pd
from datetime import datetime, timedelta
import json
import base64
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Function to extract timestamp from filename
def extract_timestamp_from_filename(filename):
    timestamp_str = filename.replace('.png', '')
    return datetime.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S-%f')

# Function to encode image to base64
def encode_image_to_base64(filepath):
    with open(filepath, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Load LIDAR data from CSV and preprocess
csv_file = 'lidar_data.csv'
df = pd.read_csv(csv_file, header=None)
df.columns = ['col0', 'timestamp', 'x', 'y', 'z', 'Reflectivity', 'Tag']
df = df.dropna(subset=['timestamp'])
df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')
df = df.dropna(subset=['timestamp'])

# Define time tolerance and image folder
tolerance = timedelta(milliseconds=50)
png_folder = 'camera_images'
results = {}

# Match images with LIDAR data and encode to base64
for filename in os.listdir(png_folder):
    if filename.endswith('.png'):
        png_filepath = os.path.join(png_folder, filename)
        png_timestamp = extract_timestamp_from_filename(filename)
        filtered_df = df[(df['timestamp'] >= png_timestamp - tolerance) & 
                         (df['timestamp'] <= png_timestamp + tolerance)]
        result_records = filtered_df[['timestamp', 'x', 'y', 'z', 'Reflectivity', 'Tag']].to_dict(orient='records')
        for record in result_records:
            record['timestamp'] = record['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f')
        image_base64 = encode_image_to_base64(png_filepath)
        results[filename] = {'image': image_base64, 'data': result_records}

# Save results to JSON
output_json = 'data_lidar_camera.json'
with open(output_json, 'w') as json_file:
    json.dump(results, json_file, indent=4)
print(f'The results are saved in {output_json}')

# Verify the saved JSON and create output folders with images and data
with open('data_lidar_camera.json', 'r') as json_file:
    data = json.load(json_file)

output_base_folder = 'output_images'
if not os.path.exists(output_base_folder):
    os.makedirs(output_base_folder)

# Create folders for the first 10 images and save decoded images and data
count = 0
for filename, content in data.items():
    if count < 10:
        image_folder = os.path.join(output_base_folder, filename.replace('.png', ''))
        os.makedirs(image_folder, exist_ok=True)
        
        image_base64 = content['image']
        image_data = base64.b64decode(image_base64)
        image_path = os.path.join(image_folder, filename)
        with open(image_path, 'wb') as image_file:
            image_file.write(image_data)

        text_path = os.path.join(image_folder, 'data.txt')
        with open(text_path, 'w') as text_file:
            for record in content['data']:
                text_file.write(f"Timestamp: {record['timestamp']}, x: {record['x']}, y: {record['y']}, z: {record['z']}, Reflectivity: {record['Reflectivity']}, Tag: {record['Tag']} \n")
    count += 1
        
print('Images and data in multiple folders')
