#ifndef UTILS
#define UTILS

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdarg.h>
#include <sys/time.h>
#include <fcntl.h>

#define DELETE_OLD_DATA_FILES 1
#define USE_CAMERA 1
#define USE_RADAR 1
#define USE_LIDAR 1


#define SAVE_CAMERA 1
#define SAVE_RADAR 1
#define SAVE_LIDAR 1


#define DURATION 1
/*
#define IMAGE_DIR "/run/media/tfe_stdu/RADAR_CAM/data/jpeg/"
#define IMAGE_EXT ".jpeg"
#define FRAME_DIR "/run/media/tfe_stdu/RADAR_CAM/data/raw/"
#define FRAME_EXT ".raw"
*/

#define IMAGE_EXT ".jpeg"
#define FRAME_EXT ".raw"
extern char IMAGE_DIR[256];
extern char FRAME_DIR[256];
extern char LIDAR_DIR[256];


extern int camera_ready;
extern int radar_ready;
extern int lidar_ready;

extern int camera_running;
extern int radar_running;
extern int start_recording;

extern int count_images;
extern int count_frames;
extern int duration;

void delete_folder_jpeg_files(char *path);
void delete_folder_raw_files(char *path);
void delete_folder_lidar_files(char *path);
char *get_filename_i(char *filename, char *root, int frame_number, char *ext);
char *get_filename_d(char *filename, char *root, double timestamp, char *ext);
char *get_filename_tv(char *filename, char *root, struct timeval tv, char *ext);
double mean(double *table, int length);
int wait_for_camera_and_radar(void);
int synchronize_end_acquisition(void);
void clock_correction(struct timeval *tv);
void start(void);
void stop(void);
void compute_NPS_camera(void);
void compute_NPS_radar(void);
void init_variables(void);

#endif
