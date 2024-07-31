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
![OpenHub-Muse Architecture Diagram (1)](https://github.com/user-attachments/assets/1fb00f06-6135-403b-97f7-c2b15824871e)

### Additional Notes
- Ensure that all IP addresses are unique within the 192.168.16.0/24 subnet to avoid conflicts.
- If any device requires a different IP address, it can be changed to any unused IP within the subnet.


# Automated Data Collection System

This project is an integrated automated data collection system that primarily runs a Shell script to start and manage multiple sensor data collection processes. The system includes camera, LiDAR, radar, and OBD (On-Board Diagnostics) modules. Data collection for each module is as follows:

- **Camera**: Captures each frame of the image and integrates it with data from other sensors.
- **LiDAR**: Transmits point cloud data via UDP protocol. Refer to Livox official documentation and SDK.
- **Radar**: Transmits data packets via TCP protocol. Refer to K-MD2 radar official documentation.
- **OBD**: Collects vehicle diagnostic data via Bluetooth connection.

## Usage Instructions

### Preparations

Note: All related program code is set up based on `laptop: openhub-Precision-3580`.

1. **Ensure the system is Linux-based**
   - This project has been tested and verified on Ubuntu systems.

2. **Install necessary Python packages**
   - Ensure the Python environment is installed and all required Python libraries are installed.

3. **The computer must support gPTP**
   - gPTP (General Precision Time Protocol) is used for time synchronization. Please refer to relevant materials for configuration.

4. **Set Bluetooth device address and related configuration files**
   - Configuration file `automotive-master.cfg` is used for gPTP master clock settings.
   - Refer to the Livox gPTP Time Synchronization Guide for specific configurations.

### Detailed Setup Steps

#### Master Clock Configuration

Configure gPTP time synchronization. Please refer to the aforementioned gPTP Time Synchronization Guide.

#### LiDAR Setup

1. Download and install Livox Viewer and Livox-SDK2.
2. Refer to the Livox LiDAR official manual and Livox-SDK2 GitHub for setup and configuration.

#### Radar Setup

Refer to the K-MD2 radar official documentation and Technical Documentation for setup.

#### Bluetooth Connection Script Setup

Write and configure scripts for Bluetooth connection to ensure successful connection with the OBD device.

#### Set Script Execution Paths

Ensure all scripts and configuration files have the correct paths.

### Running the Script

1. Navigate to the project directory:

    ```bash
    cd /path/to/your/project
    ```

2. Run the following command to start data collection:

    ```bash
    ./QuickStart.sh start
    ```

### Stopping the Script

During data collection, you can stop the script by pressing `Ctrl + C`. Stopping the script will automatically terminate all running processes and save the relevant data.

## Module Descriptions

### Camera Module

- **Startup Script**: `camera.py`
- **Function**: Collects each frame of the image and saves it to the specified directory.
- **Description**: This module starts the camera and captures images, naming and saving them according to the timestamp for subsequent data processing and analysis.

### LiDAR Module

- **Startup Script**: `livox_lidar_quick_start`
- **Function**: Transmits point cloud data via UDP protocol, monitored and recorded using tcpdump.
- **Description**: Once started, this module begins collecting point cloud data and transmits it via UDP protocol. The tcpdump tool listens to the specified port and records all transmitted data packets, generating point cloud data files.

### Radar Module

- **Startup Script**: `read_radar.py`
- **Function**: Transmits data packets via TCP protocol, monitored and recorded using tcpdump.
- **Description**: Once started, this module begins collecting radar data and transmits it via TCP protocol. The tcpdump tool listens to the specified port and records all transmitted data packets, generating radar data files.

### OBD Module

- **Startup Script**: `speed_OBD.py`
- **Function**: Connects to the OBD device via Bluetooth and collects vehicle diagnostic data.
- **Description**: Once started, this module connects to the OBD device via Bluetooth and begins collecting real-time vehicle diagnostic data. The data is saved to a specified file for subsequent analysis.

## Logs and Output

All logs and output files are stored in the specified directories. Please ensure these directories exist and have appropriate permissions. The following are the output descriptions for each module:

- **Camera Module**: Image files are named by timestamp and stored in the specified directory.
- **LiDAR Module**: Point cloud data files are stored in the specified directory, with filenames including the collection timestamp.
- **Radar Module**: Radar data files are stored in the specified directory, with filenames including the collection timestamp.
- **OBD Module**: Vehicle diagnostic data files are stored in the specified directory, with filenames including the collection timestamp.

