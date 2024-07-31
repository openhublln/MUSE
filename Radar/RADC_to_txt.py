from scapy.all import rdpcap, TCP, IP
import struct

def extract_tcp_packets(pcapng_file, target_ip):
    packets = rdpcap(pcapng_file)
    tcp_packets = [pkt for pkt in packets if TCP in pkt and pkt[IP].dst == target_ip]
    return tcp_packets

def parse_packet(packet):
    packet_info = {}

    packet_info['source_ip'] = packet[IP].src
    packet_info['destination_ip'] = packet[IP].dst  
    packet_info['packet_length'] = len(packet)
    packet_info['tcp_length'] = len(packet[TCP])
    packet_info['source_port'] = packet[TCP].sport
    packet_info['destination_port'] = packet[TCP].dport
    packet_info['seq'] = packet[TCP].seq
    packet_info['ack'] = packet[TCP].ack
    packet_info['flags'] = packet[TCP].flags
    packet_info['window'] = packet[TCP].window
    packet_info['checksum'] = packet[TCP].chksum
    packet_info['urgent_pointer'] = packet[TCP].urgptr
    payload = bytes(packet[TCP].payload)
    packet_info['payload_length'] = len(payload)

    if len(packet) == 76 and len(payload) == 8:
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

def main():
    pcapng_file = 'radar_20240729_163801.PCAP'  # Pcap path
    target_ip = '192.168.16.5'  # target IP address
    tcp_packets = extract_tcp_packets(pcapng_file, target_ip)

    with open('output_2channel.txt', 'w') as f:
        radc_data = b''
        rx_data = {'RX1': {'I': [], 'Q': []}, 'RX2': {'I': [], 'Q': []}, 'RX3': {'I': [], 'Q': []}}

        for pkt in tcp_packets:
            parsed_data = parse_packet(pkt)
            if parsed_data['header'] == 'RADC' and len(pkt) == 76:
                print(f"start parsing RADC data: {parsed_data['header']}")
            elif parsed_data['header'] is None and len(pkt) != 76: 
                radc_data += parsed_data['payload_data']
            elif parsed_data['header'] == 'DONE' and len(pkt) == 76:
                if len(radc_data) == 786432:
                    f.write(f"Sequence Number: {parsed_data['seq']}\n")
                    # Parsing RADC data
                    rx1_data = struct.unpack('<' + 'H' * 131072, radc_data[:262144])
                    rx2_data = struct.unpack('<' + 'H' * 131072, radc_data[262144:524288])
                    rx3_data = struct.unpack('<' + 'H' * 131072, radc_data[524288:786432])
                    
                    # Separating I-Channel and Q-Channel data
                    rx_data['RX1']['I'] = rx1_data[0::2]
                    rx_data['RX1']['Q'] = rx1_data[1::2]
                    rx_data['RX2']['I'] = rx2_data[0::2]
                    rx_data['RX2']['Q'] = rx2_data[1::2]
                    rx_data['RX3']['I'] = rx3_data[0::2]
                    rx_data['RX3']['Q'] = rx3_data[1::2]
                    for rx_key in rx_data:
                        f.write(f"{rx_key} I-Channel Data: {rx_data[rx_key]['I']}\n")
                        f.write(f"{rx_key} Q-Channel Data: {rx_data[rx_key]['Q']}\n") 
        
                    f.write("="*50 + "\n")
                else:
                    print(f"Error: Incomplete RADC data received. Length: {len(radc_data)} bytes\n")
                
                radc_data = b''  # Reset for next set of RADC data
        f.write("Process completed.\n")

if __name__ == "__main__":
    main()
