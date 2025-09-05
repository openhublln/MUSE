cmake_minimum_required(VERSION 3.0)

project(lidar)

# Set C++11 standard
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add dependencies
add_subdirectory(dependencies/livox-sdk2)

include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/dependencies/livox-sdk2/include
)

# Create the executables
add_executable(control src/control.cpp)
add_executable(acquisition src/acquisition.cpp)

# Link the Livox SDK library
target_link_libraries(control PUBLIC livox_lidar_sdk_static)
target_link_libraries(acquisition PUBLIC livox_lidar_sdk_static)