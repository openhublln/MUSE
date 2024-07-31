# 1.Code Explanation: combination_adjusted_lidar_infos.py

## Overview
This section of the code processes camera image files, associates them with corresponding LiDAR and speed data, and saves the results in a .json file. Each image is encoded to a base64 string, and the LiDAR data points are adjusted based on interpolated velocities.

## Detailed Steps

1. **Set up the folder paths**:
   - Set the folder paths containing the LiDAR (.csv), Camera (.png), and OBD2 (.csv) files.
   - Initialize an empty dictionary `results` to store the processed data.
   - Get a sorted list of camera files in the specified folder.

    ```python
    # Read LiDAR data
    csv_file = 'output0715.csv'
    df = pd.read_csv(csv_file, header=None, dtype=str, low_memory=False)
    df.columns = ['UTC Timestamp', 'Local Timestamp', 'X', 'Y', 'Z', 'Intensity', 'Tag Information']
    df['Local Timestamp'] = pd.to_datetime(df['Local Timestamp'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')
    df = df.dropna(subset=['Local Timestamp'])
    
    # Read speed data
    speed_file = 'speed_test.csv'
    speed_df = pd.read_csv(speed_file)
    speed_df['Time'] = pd.to_datetime(speed_df['Time'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    speed_df = speed_df.dropna(subset=['Time'])
    
    # Read camera data
    png_folder = '/home/openhub/Desktop/DATA/camera_rgba2'
    results = {}
    file_list = sorted(os.listdir(png_folder))
    ```
    
2. **Iterate Through Each Image File**:
   - Initialize `previous_filename` to `None`.
   - Loop through each file in the sorted list.
   - Get the `png_timestamp` using the function `extract_timestamp_from_filename`.

    ```python
    previous_filename = None
    for filename in file_list:
        if filename.endswith('.png'):
            png_filepath = os.path.join(png_folder, filename)
            png_timestamp = extract_timestamp_from_filename(filename)
    ```

3. **Handle the First File**:
   - Since the camera operates at 30Hz and the LiDAR is faster than the camera, the interval between the current image and the next image is around 33.3333 milliseconds.
   - Use the interval between two images to map the corresponding LiDAR timestamps.
   - If processing the first file, set `previous_timestamp` to the current file's timestamp minus 33.3333 milliseconds.

    ```python
    if previous_filename is None:
        previous_timestamp = png_timestamp - timedelta(milliseconds=33.3333)
    ```

4. **Filter LiDAR Data for the Current Timestamp Range**:
   - Filter the LiDAR DataFrame `df` to include only rows with timestamps between `previous_timestamp` and `png_timestamp`.

    ```python
    filtered_df = df[(df['Local Timestamp'] > previous_timestamp) &  
                     (df['Local Timestamp'] <= png_timestamp)]
    ```

5. **Process Each LiDAR Data Point**:
   - Initialize an empty list `updated_records` to store the adjusted LiDAR data points.
   - Iterate through each row in the filtered LiDAR DataFrame.
   - Interpolate the velocity for the current LiDAR data point's timestamp using the `interpolate_velocity` function, which performs linear interpolation.
   - If velocity interpolation returns `None`, skip the current data point (sometimes the sensor data may not be available simultaneously).
   - Adjust the X-coordinate based on the interpolated velocity and time difference.
   - Create a dictionary with the updated LiDAR data and append it to `updated_records`.

    ```python
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
    ```

6. **Encode the Image and Store the Results**:
   - Encode the current image file to a base64 string.
   - Store the encoded image and the adjusted LiDAR data in the `results` dictionary with the filename as the key.

    ```python
    image_base64 = encode_image_to_base64(png_filepath)
    results[filename] = {
        'image': image_base64,
        'data': updated_records
    }
    ```

7. **Output as JSON file**:
   - Save the `results` dictionary to a JSON file.

    ```python
    output_json = 'data_lidar_camera.json'
    with open(output_json, 'w') as json_file:
        json.dump(results, json_file, indent=4)
    ```



# 2. Code Explanation: combination_to_CSV.py

## Overview
This code follows the same logic as `combination_adjusted_lidar_infos.py` but saves the results as CSV files instead of a JSON file.

# 3. Code Explanation: open3d_Visualize.py

## Overview
This code visualizes the point cloud data.
