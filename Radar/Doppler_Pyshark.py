import struct
import numpy as np
from scipy.fftpack import fft, fftshift
from scapy.all import rdpcap, TCP, IP
import os
import pyshark
import matplotlib.pyplot as plt

def extract_tcp_packets(pcapng_file, target_ip):
    # Extract TCP packets from the pcapng file with the specified target IP address
    capture = pyshark.FileCapture(pcapng_file, display_filter=f'ip.dst == {target_ip} and tcp')
    return capture

def parse_packet(packet):
    # Parse the information from a packet and return a dictionary with the parsed data
    packet_info = {}

    packet_info['source_ip'] = packet.ip.src
    packet_info['destination_ip'] = packet.ip.dst  
    packet_info['packet_length'] = int(packet.length)
    packet_info['source_port'] = int(packet.tcp.srcport)
    packet_info['destination_port'] = int(packet.tcp.dstport)
    packet_info['seq'] = int(packet.tcp.seq)
    packet_info['ack'] = int(packet.tcp.ack)
    packet_info['flags'] = packet.tcp.flags
    packet_info['window'] = int(packet.tcp.window_size)
    packet_info['checksum'] = packet.tcp.checksum
    packet_info['urgent_pointer'] = int(packet.tcp.urgent_pointer)
    packet_info['arrival_time'] = packet.sniff_time  # Get the packet arrival time

    # Get the payload data safely
    try:
        payload = bytes.fromhex(packet.tcp.payload.replace(':', '')) if hasattr(packet.tcp, 'payload') else b''
    except AttributeError:
        payload = b''
        
    packet_info['payload_length'] = len(payload)

    if int(packet.length) == 76 and len(payload) == 8:
        header = payload[:4].decode('ascii', errors='ignore')
        payload_length = struct.unpack('<I', payload[4:8])[0]
        payload_data = payload[8:8+payload_length]
    else:
        header = None
        payload_length = None
        payload_data = payload

    packet_info.update({
        'header': header,
        'payload_length': payload_length,
        'payload_data': payload_data
    })

    return packet_info

def generate_range_doppler_map(i_data, q_data, num_samples=256):
    # Combine I and Q data to form a complex signal
    rx_data = i_data + 1j * q_data
    
    # Apply a window function to reduce spectral leakage
    window = np.hamming(num_samples)
    rx_data_windowed = rx_data * window[:,np.newaxis]

    range_doppler_map = np.fft.fft2(rx_data_windowed)
    # Only shift the velocity dimension (columns)
    range_doppler_map = np.fft.fftshift(range_doppler_map, axes=0)
    range_doppler_map = np.abs(range_doppler_map)
    range_doppler_map = np.rot90(range_doppler_map, k=1)

    return range_doppler_map

def save_range_doppler_map(range_doppler_map, filename):
    # Save the range-doppler map as an image file
    plt.figure(figsize=(10, 6))

    # Define the extent of the plot
    max_velocity = 30  # Maximum velocity in m/s
    max_range = 70  # Maximum range in meters
    num_doppler_bins = range_doppler_map.shape[1]
    num_range_bins = range_doppler_map.shape[0]
    
    # Create the velocity and range bins
    velocity_bins = np.linspace(-max_velocity, max_velocity, num_doppler_bins)
    range_bins = np.linspace(0, max_range, num_range_bins)
    
    extent = [velocity_bins.min(), velocity_bins.max(), range_bins.min(), range_bins.max()]
    
    plt.imshow(20 * np.log10(range_doppler_map), aspect='auto', cmap='jet', extent=extent)
    plt.colorbar(label='Magnitude (dB)')
    plt.title('Range-Doppler Map')
    plt.xlabel('Velocity (m/s)')
    plt.ylabel('Range (m)')
    
    # Save the figure to the specified path
    plt.savefig(filename)
    plt.close()

def main():
    pcapng_file = 'radar_20240729_163801.PCAP'  # Replace with the path to your pcapng file
    target_ip = '192.168.16.5'  # Target IP address
    tcp_packets = extract_tcp_packets(pcapng_file, target_ip)

    radc_data = b''
    rx_data = {'RX1': [], 'RX2': [], 'RX3': []}

    # Define the path to save the images
    output_directory = os.path.expanduser('~/DopplerMap_Pyshark')  # Replace with the directory path where you want to save the images
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for pkt in tcp_packets:
        parsed_data = parse_packet(pkt)
        if parsed_data['header'] == 'RADC' and len(pkt) == 76:
            print(f"Start parsing RADC data: {parsed_data['header']}")
        elif parsed_data['header'] is None and len(pkt) != 76:
            radc_data += parsed_data['payload_data']
        elif parsed_data['header'] == 'DONE' and len(pkt) == 76:
            if len(radc_data) == 786432:
                rx_data['RX1'] = struct.unpack('<' + 'H' * 131072, radc_data[:262144])
                rx_data['RX2'] = struct.unpack('<' + 'H' * 131072, radc_data[262144:524288])
                rx_data['RX3'] = struct.unpack('<' + 'H' * 131072, radc_data[524288:786432])
                print(rx_data['RX1'][:10])
                print(rx_data['RX2'][:10])
                print(rx_data['RX3'][:10])
                # Process each RX data
                for key in ['RX1', 'RX2', 'RX3']:
                    raw_data = np.array(rx_data[key])
                    i_data = raw_data[0::2].reshape((256, 256))  # I data
                    q_data = raw_data[1::2].reshape((256, 256))  # Q data
                    rx_data[key] = (i_data, q_data)

                # Generate Range-Doppler Map for each RX data
                range_doppler_map_rx1 = generate_range_doppler_map(*rx_data['RX1'])
                range_doppler_map_rx2 = generate_range_doppler_map(*rx_data['RX2'])
                range_doppler_map_rx3 = generate_range_doppler_map(*rx_data['RX3'])

                # Average Range-Doppler Maps
                mean_range_doppler_map = (range_doppler_map_rx1 + range_doppler_map_rx2 + range_doppler_map_rx3) / 3

                # Generate filename using parsed_data['seq']
                output_filename = os.path.join(output_directory, f'{parsed_data["arrival_time"]}.jpg')
                
                # Save the final Range-Doppler Map
                save_range_doppler_map(mean_range_doppler_map, output_filename)
            else:
                print(f"Error: Incomplete RADC data received. Length: {len(radc_data)} bytes")
            radc_data = b''  # Reset for the next set of RADC data

if __name__ == '__main__':
    main()
