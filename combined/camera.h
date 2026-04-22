/* Author : Ledent François, UCL, EPL (Master Thesis)
 * Date : October, June 2021
 */

/* Sources :
 * - A. Duflot, cam.c (accessed: 23/10/2021)
 * - https://www.kernel.org/doc/html/v4.10/media/uapi/v4l/v4l2.html (accessed: 30/10/2021)
 * - https://gist.github.com/maxlapshin/1253534 (accessed: 30/10/2021)
 * - https://jayrambhia.com/blog/capture-v4l2 (accessed: 23/10/2021)
 */

/* To keep in mind :
 * - sometimes delay increases -> synchronization with radar(!)
 * - select function exists (blocking when no buffer to Q, or DQ - but Q, DQ should also be blocking)
 *   https://www.kernel.org/doc/html/v4.10/media/uapi/v4l/func-select.html
 * - ...
 */

#ifndef CAMERA
#define CAMERA

#include "utils.h"

#include <stdio.h>
#include <time.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <linux/videodev2.h>

#define CAMERA_PATH "/dev/video0"

#define FRAME_WIDTH 1920
#define FRAME_LENGTH 1080
#define FRAME_PIXELFORMAT V4L2_PIX_FMT_MJPEG
#define FRAME_FIELD V4L2_FIELD_NONE

#define FRAMERATE_NUMERATOR 1
#define FRAMERATE_DENOMINATOR 30

#define N_BUFFERS 32

static struct v4l2_requestbuffers requ_buffers = {};
static struct {
    void* start;
    size_t length;
} * buffers;
static int type = V4L2_BUF_TYPE_VIDEO_CAPTURE;

int xioctl(int fh, int request, void* arg);
int open_file(void);
int display_device_information(int _file);
int display_device_crop_capabilities(int _file);
int display_available_formats(int _file);
int set_format(int _file, enum v4l2_buf_type type, unsigned int frame_width, unsigned int frame_length,
               unsigned int pixelformat, unsigned int frame_field);
int set_format_to_default(int _file);
int set_framerate(int _file, int numerator, int denominator);
int set_framerate_to_default(int _file);
int display_available_inputs(int _file);
int request_buffers(int _file);
int initialize_buffers(int _file);
void uninitialize_buffers(int _file);
int start_stream(int _file);
int stop_stream(int _file);
double get_image_real_time(struct timespec real_time, struct timespec time1, struct timeval time0);
void save_image(struct v4l2_buffer buffer);
void* main_camera(void* params);

#endif
