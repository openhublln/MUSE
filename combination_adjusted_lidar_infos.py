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
    
    before = velocity_df[velocity_df['Time'] <= target_timestamp]
    after = velocity_df[velocity_df['Time'] >= target_timestamp]

    if before.empty or after.empty:
        return None  # No valid velocity data for interpolation

    closest_before = before.iloc[-1]
    closest_after = after.iloc[0]

    if closest_before['Time'] == closest_after['Time']:
        return closest_before['Speed (km/h)']
    else:
        time_diff = (closest_after['Time'] - closest_before['Time']).total_seconds()
        ratio = (target_timestamp - closest_before['Time']).total_seconds() / time_diff
        vx = closest_before['Speed (km/h)'] + ratio * (closest_after['Speed (km/h)'] - closest_before['Speed (km/h)'])
        return vx
    

# Lire les données LiDAR
csv_file = 'output7_8.csv'
df = pd.read_csv(csv_file, header=None, dtype=str, low_memory=False)
df.columns = ['UTC Timestamp', 'Local Timestamp', 'X', 'Y', 'Z', 'Intensity', 'Tag Information']
#df = df.dropna(subset=['timestamp'])
df['Local Timestamp'] = pd.to_datetime(df['Local Timestamp'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')
df = df.dropna(subset=['Local Timestamp'])

# Lire les données de vitesse
speed_file = '/home/openhub/Downloads/speed_test.csv'
speed_df = pd.read_csv(speed_file)
speed_df['Time'] = pd.to_datetime(speed_df['Time'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
speed_df = speed_df.dropna(subset=['Time'])



png_folder = '/home/openhub/Desktop/Parse_UDP/DATA/camera_rgba'
results = {}
file_list = sorted(os.listdir(png_folder))

previous_filename = None
for filename in file_list:
    if filename.endswith('.png'):
        png_filepath = os.path.join(png_folder, filename)
        png_timestamp = extract_timestamp_from_filename(filename)
        if previous_filename is None:
            previous_timestamp = png_timestamp - timedelta(milliseconds=33.3333)
        filtered_df = df[(df['Local Timestamp'] > previous_timestamp) &  
                         (df['Local Timestamp'] <= png_timestamp)]  
        
        #print("PNG TIMESTAMP:"+str(png_timestamp))
        #print(str(previous_timestamp)+"-"+str(png_timestamp))
        #print(filtered_df)

        updated_records = [] 
        for _, row in filtered_df.iterrows():
            target_timestamp = row['Local Timestamp']
            vx = interpolate_velocity(speed_df, target_timestamp)
            if vx is None:
                continue
            time_diff = (target_timestamp - png_timestamp).total_seconds()
            new_x = str(float(row['X']) + float(vx * time_diff))
            updated_record = {
                'timestamp': target_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f'),
                'x': new_x,
                'y': row['X'],
                'z': row['Z'],
                'Reflectivity': row['Intensity'],
                'Tag': row['Tag Information'],
                'Speed': vx
            }
            updated_records.append(updated_record)
   

        image_base64 = encode_image_to_base64(png_filepath)
        results[filename] = {
            'image': image_base64,
            'data': updated_records
        }

        previous_filename = filename
        previous_timestamp = png_timestamp


output_json = 'data_lidar_camera.json'
with open(output_json, 'w') as json_file:
    json.dump(results, json_file, indent=4)


print(f'The results are saved in {output_json}')
