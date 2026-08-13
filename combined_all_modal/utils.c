#include "utils.h"

char IMAGE_DIR[256];
char FRAME_DIR[256];
char LIDAR_DIR[256];

void delete_folder_jpeg_files(char *path) {
    char command_line[200] = "exec rm -r ";
    strcpy(&command_line[11], path);
    strcpy(&command_line[11 + strlen(path)], "*.jpeg");

    system(command_line);
    printf("\nJPEG files from %s deleted.\n", path, command_line);
}

void print_time(const char *msg)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);

    printf("[%.3f] %s\n",
           ts.tv_sec + ts.tv_nsec / 1e9,
           msg);
    fflush(stdout);
}

void delete_folder_raw_files(char *path) {
    char command_line[200] = "exec rm -r ";
    strcpy(&command_line[11], path);
    strcpy(&command_line[11 + strlen(path)], "*.raw");

    system(command_line);
    printf("\nRAW files from %s deleted.\n", path, command_line);
}

void delete_folder_lidar_files(char *path) {
    char command_line[200] = "exec rm -r ";
    strcpy(&command_line[11], path);
    strcpy(&command_line[11 + strlen(path)], "*.ply");

    system(command_line);
    printf("\nLiDAR files from %s deleted.\n", path);
}

char *get_filename_i(char *filename, char *root, int frame_number, char *ext) {
    char _timestamp[32];
    unsigned int _len_root = strlen(root);
    unsigned int _len_timestamp = _len_root + sprintf(_timestamp, "%05d", frame_number);

    strcpy(filename, root);
    strcpy(&filename[_len_root], _timestamp);
    strcpy(&filename[_len_timestamp], ext);

    return filename;
}

char *get_filename_d(char *filename, char *root, double timestamp, char *ext) {
    char _timestamp[32];
    unsigned int _len_root = strlen(root);
    unsigned int _len_timestamp = _len_root + sprintf(_timestamp, "%018f", timestamp);

    strcpy(filename, root);
    strcpy(&filename[_len_root], _timestamp);
    strcpy(&filename[_len_timestamp], ext);

    return filename;
}

char *get_filename_tv(char *filename, char *root, struct timeval tv, char *ext) {
    char _timestamp[32];
    unsigned int _len_root = strlen(root);
    unsigned int _len_timestamp = _len_root + sprintf(_timestamp, "%0d.%06d", tv.tv_sec, tv.tv_usec);

    strcpy(filename, root);
    strcpy(&filename[_len_root], _timestamp);
    strcpy(&filename[_len_timestamp], ext);

    return filename;
}

double mean(double *table, int length) {
    double _sum;
    for (int i = 0; i < length; i++) {
        _sum += table[i];
    }
    return _sum / length;
}

int wait_for_camera_and_radar(void) {

    uint8_t sensors = 0;

    if (USE_CAMERA)
    {
        sensors |= SENSOR_CAMERA;
    }

    if (USE_RADAR)
    {
        sensors |= SENSOR_RADAR;
    }

    if (USE_LIDAR)
    {
        sensors |= SENSOR_LIDAR;
    }


    while (1)
    {
        if ((!(sensors & SENSOR_CAMERA) || camera_ready) &&
            (!(sensors & SENSOR_RADAR)  || radar_ready)  &&
            (!(sensors & SENSOR_LIDAR)  || lidar_ready))
        {
            break;
        }

        usleep(5000);
    }

    return 0;
}



void clock_correction(struct timeval *tv) {
    while ((int)tv->tv_usec < 0) {
        tv->tv_usec += 1000000;
        tv->tv_sec -= 1;
    }

    while ((int)tv->tv_usec >= 1000000) {
        tv->tv_usec -= 1000000;
        tv->tv_sec += 1;
    }
}

struct timeval _start_tv, _stop_tv, _diff_tv;
void start(void) {
    gettimeofday(&_start_tv, NULL);
}

void stop(void) {
    gettimeofday(&_stop_tv, NULL);
    _diff_tv.tv_sec = _stop_tv.tv_sec-_start_tv.tv_sec;
    _diff_tv.tv_usec = _stop_tv.tv_usec-_start_tv.tv_usec;

    if (_diff_tv.tv_usec < 0) {
        _diff_tv.tv_sec -= 1;
        _diff_tv.tv_usec += 1000000;
    }

    printf("elapsed time : %d, %06d\n", _diff_tv.tv_sec, _diff_tv.tv_usec);
}

int count_camera = 0;
int sec_camera = 0, nps_camera = 1;
struct timeval nps_tv_camera;
void compute_NPS_camera(void) {
  gettimeofday(&nps_tv_camera, NULL);

  if ((int)(nps_tv_camera.tv_sec) != sec_camera) {
    printf("[%03d] nimages %d\n", count_camera, nps_camera);
    nps_camera = 1;
    sec_camera = (int)(nps_tv_camera.tv_sec);
    count_camera += 1;
  }
  else {
    nps_camera += 1;
  }
}

int count_radar = 0;
int sec_radar = 0, nps_radar = 1;
struct timeval nps_tv_radar;
void compute_NPS_radar(void) {
  gettimeofday(&nps_tv_radar, NULL);

  if ((int)(nps_tv_radar.tv_sec) != sec_radar) {
    printf("                      [%03d] nframes %d\n", count_radar, nps_radar);
    nps_radar = 1;
    sec_radar = (int)(nps_tv_radar.tv_sec);
    count_radar += 1;
  }
  else {
    nps_radar += 1;
  }
}

int camera_ready = 0;
int radar_ready = 0;
int lidar_ready = 0;
int lidar_control_done = 0;
int radar_initialisation = 0;
int count_images = 0;
int count_frames = 0;

void init_variables(void) {
}
