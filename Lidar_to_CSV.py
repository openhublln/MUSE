import pyshark
import struct
from datetime import datetime, timedelta
import csv
import os

def create_output_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def parse_lidar_payload(payload):
    """
    解析LiDAR点云协议的Payload数据，根据提供的格式进行解析。
    """
    try:
        # 解析各个字段
        version = struct.unpack('B', payload[0:1])[0]
        length = struct.unpack('>H', payload[1:3])[0]
        time_interval = struct.unpack('>H', payload[3:5])[0]
        dot_num = struct.unpack('>H', payload[5:7])[0]
        udp_cnt = struct.unpack('>H', payload[7:9])[0]
        frame_cnt = struct.unpack('B', payload[9:10])[0]
        data_type = struct.unpack('B', payload[10:11])[0]
        time_type = struct.unpack('B', payload[11:12])[0]
        pack_info = struct.unpack('B', payload[12:13])[0]
        resv = payload[13:24]  # 保留字段，长度为11字节
        crc32 = struct.unpack('>I', payload[24:28])[0]
        timestamp = struct.unpack('Q', payload[28:36])[0]  # >Q unsigned long long
        data = payload[36:]  # 剩余数据

        return {
            "version": version,
            "length": length,
            "time_interval": time_interval,
            "dot_num": dot_num,
            "udp_cnt": udp_cnt,
            "frame_cnt": frame_cnt,
            "data_type": data_type,
            "time_type": time_type,
            "pack_info": pack_info,
            "resv": resv,
            "crc32": crc32,
            "timestamp": timestamp,
            "data": data
        }
    except Exception as e:
        print(f"Error parsing payload: {e}")
        return None

def parse_lidar_data(data):
    """
    解析点云数据，假设每个点包含x, y, z坐标和强度值，每个坐标和强度值都是int和2个uint8类型。
    """
    point_size = 14  # 每个点包含4个float（x, y, z, intensity）
    num_points = len(data) // point_size
    point_format = 'iiiBB'  # struct格式：3个int 2个uint8 = 14BYTES

    points = []

    for i in range(num_points):
        offset = i * point_size
        point = struct.unpack(point_format, data[offset:offset + point_size])
        points.append({
            'x': point[0] / 1000,
            'y': point[1] / 1000,
            'z': point[2] / 1000,
            'intensity': point[3],
            'tag_information': point[4]
        })
    return points

def Formatted_Realtime(value):
    value = value / 1e9
    epoch = datetime(1970, 1, 1)
    timestamp_datetime = epoch + timedelta(seconds=value)
    return timestamp_datetime

#output_folder = 'Lidar'
#create_output_folder(output_folder)
#output_file = os.path.join(output_folder, 'output.csv')

with open('output.csv', 'w', newline='') as csvfile:
    fieldnames = ['UTC Timestamp', 'Local Timestamp', 'X', 'Y', 'Z', 'Intensity', 'Tag Information']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # 读取PCAP文件
    cap = pyshark.FileCapture('capture.pcap', display_filter='udp')

    # 遍历封包并显示信息
    for packet in cap:
        try:
            # 检查是否有负载信息
            if hasattr(packet.udp, 'payload'):
                payload = packet.udp.payload.binary_value
                parsed_payload = parse_lidar_payload(payload)
                if parsed_payload:
                    UTC_Timestamp = Formatted_Realtime(parsed_payload['timestamp'])
                    Local_Timestamp = UTC_Timestamp + timedelta(hours=2)
                    print(Local_Timestamp)
                    print("-"*50)
                    points = parse_lidar_data(parsed_payload['data'])
                    for point in points:
                        row = {
                            'UTC Timestamp': UTC_Timestamp,
                            'Local Timestamp': Local_Timestamp,
                            'X': point['x'],
                            'Y': point['y'],
                            'Z': point['z'],
                            'Intensity': point['intensity'],
                            'Tag Information': point['tag_information']
                        }
                        writer.writerow(row)
            else:
                # 没有负载时的占位符处理（可选）
                row = {
                    'UTC Timestamp': 'No payload available',
                    'Local Timestamp': 'No payload available',
                    'X': 'No payload available',
                    'Y': 'No payload available',
                    'Z': 'No payload available',
                    'Intensity': 'No payload available',
                    'Tag Information': 'No payload available',
                }
                writer.writerow(row)
                print("end")
        except AttributeError as e:
            continue

print("Data has been saved to output.csv.")