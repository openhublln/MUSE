// TODO: verify the license and copyright
//
// The MIT License (MIT)
//
// Copyright (c) 2022 Livox. All rights reserved.
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
//

#include "livox_lidar_def.h"
#include "livox_lidar_api.h"

#include <arpa/inet.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <iostream>
#include <mutex>
#include <condition_variable>
#include <csignal>
#include <unistd.h>
#include <time.h>

void print_time(const char *msg)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);

    printf("[%.3f] %s\n",
           ts.tv_sec + ts.tv_nsec / 1e9,
           msg);
    fflush(stdout);
}

struct point_cloud_callback_arg {
  uint frequency_hz;
  std::string output_dir;
  int ready_pipe_fd;
  int go_pipe_fd;

};

struct point_buf {
    u_int64_t first_timestamp; // time of first point in buf in ns
    uint32_t size;
    LivoxLidarCartesianHighRawPoint points[500000]; // lisdar speed 452000 points/s, ~1s buffer
};
  
std::condition_variable quit_condition;

struct point_buf g_point_buf = {0};

void Stop(int signal) {
  printf("Stopping by signal %d\n", signal);
  quit_condition.notify_all();
}

void DumpPointBuf(std::string output_dir) {
    if (g_point_buf.size == 0) {
        return;
    }
    char filename[128] = {0};
    snprintf(filename, sizeof(filename), "%s/%lu.ply", output_dir.c_str(), g_point_buf.first_timestamp);
    FILE* fp = fopen(filename, "w");
    if (fp == nullptr) {
        fprintf(stderr, "open file %s failed\n", filename);
        return;
    }

    // write ply header
    fprintf(fp, "ply\n\
format binary_little_endian 1.0\n\
element vertex %u\n\
property int x\n\
property int y\n\
property int z\n\
property uchar reflectivity\n\
property uchar tag\n\
end_header\n", g_point_buf.size);
    // write point data
    fwrite(g_point_buf.points, sizeof(LivoxLidarCartesianHighRawPoint), g_point_buf.size, fp);
    fclose(fp);
}

void PointCloudCallback(uint32_t handle, const uint8_t dev_type, LivoxLidarEthernetPacket* data, void* client_data) {
  if (data == nullptr) {
    return;
  }


  point_cloud_callback_arg* arg = (point_cloud_callback_arg*)client_data;

  u_int64_t timestamp = *((u_int64_t*)data->timestamp);

  static bool first = true;

  if (first) {
      first = false;
      print_time("first packet receive");
      printf("Timestamp type : %u\n", data->time_type);
      printf("Timestamp      : %lu\n", timestamp);

      if (data->time_type == 1){
          printf(">>> PTP/gPTP synchronization detected <<<\n");
          }
      else
          printf(">>> WARNING : NOT using PTP/gPTP <<<\n");

      /* -------- Synchronisation -------- */
      print_time("Sending READY to parent");
      char ready = 'R';
      if (write(arg->ready_pipe_fd, &ready, 1) != 1)
      {
          perror("write READY");
          return;
      }
      close(arg->ready_pipe_fd);

      print_time("Waiting GO...");
      char go;
      if (read(arg->go_pipe_fd, &go, 1) != 1)
      {
          perror("read GO");
          return;
      }
      close(arg->go_pipe_fd);
      print_time("GO received");
  }
  
  if (g_point_buf.first_timestamp == 0) {
    g_point_buf.first_timestamp = timestamp;
    g_point_buf.size = 0;
  } else if (timestamp - g_point_buf.first_timestamp > 1000000000 / arg->frequency_hz) {
    DumpPointBuf(arg->output_dir);
    g_point_buf.first_timestamp = timestamp;
    g_point_buf.size = 0;
  }

  if (data->data_type == kLivoxLidarCartesianCoordinateHighData) {
    LivoxLidarCartesianHighRawPoint *p_point_data = (LivoxLidarCartesianHighRawPoint *)data->data;
    memcpy(g_point_buf.points + g_point_buf.size, p_point_data, data->dot_num * sizeof(LivoxLidarCartesianHighRawPoint));
    g_point_buf.size += data->dot_num;
  }else {
    fprintf(stderr, "Error this program only support CartesianCoordinateHigh");
    exit(1); // TODO: clean up before exit
  }
}

void ImuDataCallback(uint32_t handle, const uint8_t dev_type,  LivoxLidarEthernetPacket* data, void* client_data) {
  if (data == nullptr) {
    return;
  } 
  printf("Imu data callback handle:%u, data_num:%u, data_type:%u, length:%u, frame_counter:%u.\n",
      handle, data->dot_num, data->data_type, data->length, data->frame_cnt);
}

void WorkModeCallback(livox_status status, uint32_t handle,LivoxLidarAsyncControlResponse *response, void *client_data) {
  if (response == nullptr) {
    return;
  }
  printf("WorkModeCallack, status:%u, handle:%u, ret_code:%u, error_key:%u",
      status, handle, response->ret_code, response->error_key);

}

void QueryInternalInfoCallback(livox_status status, uint32_t handle, 
    LivoxLidarDiagInternalInfoResponse* response, void* client_data) {
  if (status != kLivoxLidarStatusSuccess) {
    printf("Query lidar internal info failed.\n");
    QueryLivoxLidarInternalInfo(handle, QueryInternalInfoCallback, nullptr);
    return;
  }

  if (response == nullptr) {
    return;
  }

  uint8_t host_point_ipaddr[4] {0};
  uint16_t host_point_port = 0;
  uint16_t lidar_point_port = 0;

  uint8_t host_imu_ipaddr[4] {0};
  uint16_t host_imu_data_port = 0;
  uint16_t lidar_imu_data_port = 0;

  uint16_t off = 0;
  for (uint8_t i = 0; i < response->param_num; ++i) {
    LivoxLidarKeyValueParam* kv = (LivoxLidarKeyValueParam*)&response->data[off];
    if (kv->key == kKeyLidarPointDataHostIpCfg) {
      memcpy(host_point_ipaddr, &(kv->value[0]), sizeof(uint8_t) * 4);
      memcpy(&(host_point_port), &(kv->value[4]), sizeof(uint16_t));
      memcpy(&(lidar_point_port), &(kv->value[6]), sizeof(uint16_t));
    } else if (kv->key == kKeyLidarImuHostIpCfg) {
      memcpy(host_imu_ipaddr, &(kv->value[0]), sizeof(uint8_t) * 4);
      memcpy(&(host_imu_data_port), &(kv->value[4]), sizeof(uint16_t));
      memcpy(&(lidar_imu_data_port), &(kv->value[6]), sizeof(uint16_t));
    }
    else if (kv->key == kKeyWorkMode) {
        uint8_t mode = *(uint8_t*)kv->value;
        printf("[WORK_MODE] %u\n", mode);
    }
    else if (kv->key == kKeyCurWorkState) {
        uint8_t state = *(uint8_t*)kv->value;
        printf("[CURRENT_WORK_STATE] %u\n", state);
    }    

    off += sizeof(uint16_t) * 2;
    off += kv->length;
    }

  printf("Host point cloud ip addr:%u.%u.%u.%u, host point cloud port:%u, lidar point cloud port:%u.\n",
      host_point_ipaddr[0], host_point_ipaddr[1], host_point_ipaddr[2], host_point_ipaddr[3], host_point_port, lidar_point_port);

  printf("Host imu ip addr:%u.%u.%u.%u, host imu port:%u, lidar imu port:%u.\n",
    host_imu_ipaddr[0], host_imu_ipaddr[1], host_imu_ipaddr[2], host_imu_ipaddr[3], host_imu_data_port, lidar_imu_data_port);

}

void LidarInfoChangeCallback(const uint32_t handle, const LivoxLidarInfo* info, void* client_data) {
  if (info == nullptr) {
    printf("lidar info change callback failed, the info is nullptr.\n");
    return;
  } 
  printf("LidarInfoChangeCallback Lidar handle: %u SN: %s\n", handle, info->sn);
  
  // set the work mode to kLivoxLidarNormal, namely start the lidar
  SetLivoxLidarWorkMode(handle, kLivoxLidarNormal, WorkModeCallback, nullptr);

  QueryLivoxLidarInternalInfo(handle, QueryInternalInfoCallback, nullptr);
}

void LivoxLidarPushMsgCallback(const uint32_t handle, const uint8_t dev_type, const char* info, void* client_data) {
  struct in_addr tmp_addr;
  tmp_addr.s_addr = handle;  
  //std::cout << "handle: " << handle << ", ip: " << inet_ntoa(tmp_addr) << ", push msg info: " << std::endl;
  //std::cout << info << std::endl;
  return;
}

int main(int argc, const char *argv[]) {
  printf("argc = %d\n", argc);

  for (int i = 0; i < argc; i++)
  {
      printf("argv[%d] = '%s'\n", i, argv[i]);
  }
  fflush(stdout);
  
  if (argc != 6) {
    fprintf(stderr, "usage: acquisition <config_file_path> <frequency_hz> <output_dir> <ready_fd> <go_fd>\n");
    return -1;
  }
  const std::string path = argv[1];
  const uint frequency_hz = atoi(argv[2]);
  const std::string output_dir = argv[3];
  const int ready_pipe_fd = atoi(argv[4]);
  const int go_pipe_fd    = atoi(argv[5]);


  // REQUIRED, to init Livox SDK2
  if (!LivoxLidarSdkInit(path.c_str())) {
    printf("Livox Init Failed\n");
    LivoxLidarSdkUninit();
    return -1;
  }
  print_time("SDK initialized");


  point_cloud_callback_arg arg = {frequency_hz, output_dir,ready_pipe_fd,go_pipe_fd};

  // REQUIRED, to get point cloud data via 'PointCloudCallback'
  SetLivoxLidarPointCloudCallBack(PointCloudCallback, &arg);

  // OPTIONAL, to get imu data via 'ImuDataCallback'
  // some lidar types DO NOT contain an imu component
//   SetLivoxLidarImuDataCallback(ImuDataCallback, nullptr);
  
  SetLivoxLidarInfoCallback(LivoxLidarPushMsgCallback, nullptr);
  
  // REQUIRED, to get a handle to targeted lidar and set its work mode to NORMAL
  SetLivoxLidarInfoChangeCallback(LidarInfoChangeCallback, nullptr);

  // wait for crtl + c or terminate signal
  std::signal(SIGINT, Stop);
  std::signal(SIGTERM, Stop);

  std::mutex quit_mutex;
  std::unique_lock<std::mutex> lock(quit_mutex);
  quit_condition.wait(lock);

  LivoxLidarSdkUninit();
  printf("Acquisition Ended\n");
  return 0;
}

