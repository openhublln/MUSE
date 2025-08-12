import struct
import time
from scapy.all import sniff, UDP, Raw
import os

# Point format: x, y, z (int32), reflectivity (uint8), tag (uint8)
POINT_STRUCT = struct.Struct('<iiiBB')

points = []
last_write_time = time.time()
PLY_WRITE_INTERVAL = 5  # seconds

def write_ply(filename, points):
    with open(filename, 'w') as f:
        f.write("ply\nformat ascii 1.0\n")
        f.write(f"element vertex {len(points)}\n")
        f.write("property int x\nproperty int y\nproperty int z\n")
        f.write("property uchar reflectivity\nproperty uchar tag\n")
        f.write("end_header\n")
        for p in points:
            f.write(f"{p[0]} {p[1]} {p[2]} {p[3]} {p[4]}\n")

def packet_handler(pkt, save_folder):
    global points, last_write_time

    if UDP in pkt and pkt[UDP].dport == 57000:
        raw_data = bytes(pkt[Raw])
        num_points = len(raw_data) // 14
        for i in range(num_points):
            start = i * 14
            point = POINT_STRUCT.unpack(raw_data[start:start+14])
            points.append(point)

        now = time.time()
        if now - last_write_time > PLY_WRITE_INTERVAL:
            timestamp = int(now)
            filename = os.path.join(save_folder, f"live_pointcloud_{timestamp}.ply")
            write_ply(filename, points)
            print(f"Saved {len(points)} points to {filename}")
            last_write_time = now

def start_sniffing(save_folder):
    sniff(filter="udp port 57000", prn=lambda pkt: packet_handler(pkt, save_folder), store=False)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python lidar_live_ply.py <save_folder>")
        exit(1)
    folder = sys.argv[1]
    os.makedirs(folder, exist_ok=True)
    print(f"Starting live LiDAR capture, saving PLY files to: {folder}")
    start_sniffing(folder)
