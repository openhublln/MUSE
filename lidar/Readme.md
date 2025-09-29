# Lidar Controller and Acquisition

This directory contains the code for controlling a Lidar sensor and acquiring data from it. The code is organized into several files, each responsible for different aspects of the Lidar operation.

## Dependencies

This code uses the Livox SDK2 for communication with the Lidar. It is a submodule of this repository, so you need to clone the repository with the `--recurse-submodules` flag.

## Building

To build the code, you need to have CMake and a compatible C++ compiler installed. You can then create a build directory and run CMake to generate the build files.

```bash
mkdir build
cd build
cmake ..
make
```
This will create two executables:
- control: to change the Lidar state `usage: control <config_file_path> <start|stop>`
- acquisition: to acquire point clouds `usage: acquisition <config_file_path> <frequency_hz> <output_dir>`