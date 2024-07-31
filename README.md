# Muse
muse

## Network Setup Instructions

### Overview
This document provides instructions for setting up the network configuration for several devices, including LiDAR, radar, and a laptop. The devices will be connected via a wired network to a switch, establishing an internal network using the 192.168.16.0/24 subnet. Detailed steps and configurations are provided below.

### Steps

1. **Connecting Devices**:
   - Connect the LiDAR, radar, and laptop to the switch using Ethernet cables.
   - Ensure all devices are properly powered and connected to the switch.

2. **Network Configuration**:
   - **Radar**:
     - The radar will use its default IP address: `192.168.16.2`.
   - **LiDAR**:
     - Use the Livox Viewer 2 software to modify the default IP address of the LiDAR.
     - Set the IP address to: `192.168.16.100`.
   - **Laptop**:
     - Configure the laptop to use a manual IP address.
     - Set the IP address to: `192.168.16.5`.
   - **Other Devices**:
     - Cameras will be connected via USB.
     - The OBD2 device will connect directly to the laptop using Bluetooth.

### Diagram
![OpenHub-Muse Architecture Diagram](https://github.com/user-attachments/assets/f17ffaf8-5cfe-4070-aef8-1aa9d57adef6)
### Additional Notes
- Ensure that all IP addresses are unique within the 192.168.16.0/24 subnet to avoid conflicts.
- If any device requires a different IP address, it can be changed to any unused IP within the subnet.
