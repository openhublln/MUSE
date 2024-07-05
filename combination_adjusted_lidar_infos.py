import os
import pandas as pd
from datetime import datetime, timedelta
import json
import base64
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def extract_timestamp_from_filename(filename):
    timestamp_str = filename.replace('.png', '')
    return datetime.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S-%f')

def encode_image_to_base64(filepath):
    with open(filepath, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def interpolate_velocity(velocity_df, target_timestamp):
    closest_before = velocity_df[velocity_df['timestamp'] <= target_timestamp].iloc[-1]
    closest_after = velocity_df[velocity_df['timestamp'] >= target_timestamp].iloc[0]

    if closest_before['timestamp'] == closest_after['timestamp']:
        return closest_before['vx']
    else:
        time_diff = (closest_after['timestamp'] - closest_before['timestamp']).total_seconds()
        ratio = (target_timestamp - closest_before['timestamp']).total_seconds() / time_diff
        vx = closest_before['vx'] + ratio * (closest_after['vx'] - closest_before['vx'])
        return vx

# Lire les données LiDAR
csv_file = 'lidar_data.csv'
df = pd.read_csv(csv_file, header=None)
df.columns = ['col0', 'timestamp', 'x', 'y', 'z', 'Reflectivity', 'Tag']
df = df.dropna(subset=['timestamp'])
df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')
df = df.dropna(subset=['timestamp'])

# Lire les données de vitesse
speed_file = 'speed_data.csv'
speed_df = pd.read_csv(speed_file)
speed_df['timestamp'] = pd.to_datetime(speed_df['timestamp'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')
speed_df = speed_df.dropna(subset=['timestamp'])

# Tolérance pour la correspondance des timestamps
tolerance = timedelta(milliseconds=50)

png_folder = 'camera_images'
results = {}

for filename in os.listdir(png_folder):
    if filename.endswith('.png'):
        png_filepath = os.path.join(png_folder, filename)
        png_timestamp = extract_timestamp_from_filename(filename)
        filtered_df = df[(df['timestamp'] >= png_timestamp - tolerance) & 
                         (df['timestamp'] <= png_timestamp + tolerance)]
        
        # Mettre à jour les coordonnées x en fonction de la vitesse
        updated_records = []
        for _, row in filtered_df.iterrows():
            vx = interpolate_velocity(speed_df, row['timestamp'])
            time_diff = (row['timestamp'] - png_timestamp).total_seconds()
            new_x = row['x'] + vx * time_diff
            updated_record = {
                'timestamp': row['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f'),
                'x': new_x,
                'y': row['y'],
                'z': row['z'],
                'Reflectivity': row['Reflectivity'],
                'Tag': row['Tag']
            }
            updated_records.append(updated_record)
        
        image_base64 = encode_image_to_base64(png_filepath)
        results[filename] = {
            'image': image_base64,
            'data': updated_records
        }

output_json = 'data_lidar_camera.json'
with open(output_json, 'w') as json_file:
    json.dump(results, json_file, indent=4)

print(f'The results are saved in {output_json}')
