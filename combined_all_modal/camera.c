#include "camera.h"

int xioctl(int fh, int request, void *arg) {
    int res;
    do {
        res = ioctl(fh, request, arg);
    } while (res == -1 && EINTR == errno);
    return res;
}

int open_file(void) {
    int _file;
    if ((_file = open(CAMERA_PATH, O_RDWR)) < 0) {
        perror("Opening");
        return -1;
    }
    return _file;
}

int display_device_information(int _file) {
    struct v4l2_capability cap = {};
    if (xioctl(_file, VIDIOC_QUERYCAP, &cap) == -1) {
        perror("Querying Capabilities");
        return -1;
    }

    printf("\nDEVICE INFORMATION\n");
    printf("-driver : %s\n", cap.driver);
    printf("-card : %s\n", cap.card);
    printf("-bus_info : %s\n", cap.bus_info);
    printf("-version : %d.%d\n",
           (cap.version >> 16) && 0xFF,
           (cap.version >> 24) && 0xFF);
    printf("-capabilities (flags) : 0x%x\n", cap.capabilities);
    printf("-device_caps (flags): 0x%x\n", cap.device_caps);

    return 0;
}

int display_device_crop_capabilities(int _file) {
    struct v4l2_cropcap cropcap = {};
    cropcap.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;

    if (xioctl(_file, VIDIOC_CROPCAP, &cropcap) == -1) {
        perror("Querying Cropping Capabilities");
        return -1;
    }

    printf("\nDEVICE CROP CAPABILITIES\n");
    printf("-bounds : %dx%d+%d+%d\n",
           cropcap.bounds.width, cropcap.bounds.height,
           cropcap.bounds.left, cropcap.bounds.top);
    printf("-default : %dx%d+%d+%d\n",
           cropcap.defrect.width, cropcap.defrect.height,
           cropcap.defrect.left, cropcap.defrect.top);
    printf("-aspect : %d/%d\n", cropcap.pixelaspect.numerator,
           cropcap.pixelaspect.denominator);

    return 0;
}

int display_available_formats(int _file) {
    struct v4l2_fmtdesc fmtdesc = {};
    char _cpy[5] = {};

    printf("\nAVAILABLE FORMATS\n");
    fmtdesc.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    while (xioctl(_file, VIDIOC_ENUM_FMT, &fmtdesc) == 0) {
        strncpy(_cpy, (char *)&fmtdesc.pixelformat, 4);
        printf("-format %i : %s, %x, %s\n", fmtdesc.index,
               _cpy, fmtdesc.flags, fmtdesc.description);
        fmtdesc.index++;
    }

    return 0;
}

int set_format(int _file, enum v4l2_buf_type type, unsigned int frame_width, unsigned int frame_length,
               unsigned int pixelformat, unsigned int frame_field) {
    struct v4l2_format fmt = {};
    fmt.type = type;
    fmt.fmt.pix.width = frame_width;
    fmt.fmt.pix.height = frame_length;
    fmt.fmt.pix.pixelformat = pixelformat;
    fmt.fmt.pix.field = frame_field;

    printf("\nSETTING FORMAT\n");
    if (xioctl(_file, VIDIOC_S_FMT, &fmt) == -1) {
        perror("Setting Pixel Format");
        return -1;
    }

    return 0;
}

int set_format_to_default(int _file) {
    set_format(_file, V4L2_BUF_TYPE_VIDEO_CAPTURE, FRAME_WIDTH, FRAME_LENGTH,
               FRAME_PIXELFORMAT, FRAME_FIELD);
}

int set_framerate(int _file, int numerator, int denominator) {
    struct v4l2_streamparm streamparm = {};
    streamparm.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    //streamparm.parm.capture.timeperframe.numerator = numerator;
    //streamparm.parm.capture.timeperframe.denominator = denominator;
    
    if (ioctl(_file, VIDIOC_S_PARM, &streamparm) == -1) {
        perror("VIDIOC_S_PARM");
    }

    struct v4l2_format format = {};

    format.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    if (ioctl(_file, VIDIOC_G_FMT, &format) == -1) {
        perror("VIDIOC_G_FMT");
        return -1;
    }

    printf("%dx%d %c%c%c%c %2.2ffps\n",
           format.fmt.pix.width, format.fmt.pix.height,
           (format.fmt.pix.pixelformat >> 0) & 0xff,
           (format.fmt.pix.pixelformat >> 8) & 0xff,
           (format.fmt.pix.pixelformat >> 16) & 0xff,
           (format.fmt.pix.pixelformat >> 24) & 0xff,
           (float)streamparm.parm.capture.timeperframe.denominator /
               (float)streamparm.parm.capture.timeperframe.numerator);

    return 0;
}

int set_framerate_to_default(int _file) {
    set_framerate(_file, FRAMERATE_NUMERATOR, FRAMERATE_DENOMINATOR);
}

int display_available_inputs(int _file) {
    struct v4l2_input input = {};

    int current_input_index;
    if (ioctl(_file, VIDIOC_G_INPUT, &current_input_index) != 0) {
        perror("Getting current input");
        return -1;
    }

    printf("\nAVAILABLE INPUTS (curr. input ind. : %d)\n", current_input_index);
    input.index = 0;
    while ((ioctl(_file, VIDIOC_ENUMINPUT, &input)) == 0) {
        printf("Input index : %d\n", input.index);
        printf("-name: %s\n", input.name);
        printf("-type: %i\n", input.type);
        printf("-status: %x\n", input.status);
        printf("-capabilities: %x\n", input.capabilities);
        input.index++;
    }
}

int request_buffers(int _file) {
    requ_buffers.count = N_BUFFERS;
    requ_buffers.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    requ_buffers.memory = V4L2_MEMORY_MMAP;

    if (ioctl(_file, VIDIOC_REQBUFS, &requ_buffers) != 0) {
        perror("Requesting buffers");
        return -1;
    }

    printf("\nREQUESTING BUFFERS\n");
    printf("-number : %d (asked : %d)\n", requ_buffers.count, N_BUFFERS);
    printf("-type : %d\n", requ_buffers.type);
    printf("-memory type : %d\n", requ_buffers.memory);

    return 0;
}

int initialize_buffers(int _file) {
    /* allocating memory */
    if ((buffers = calloc(requ_buffers.count, sizeof(*buffers))) == NULL) {
        perror("Allocating memory for buffers");
        return -1;
    }

    /* queying and instantiating buffers */
    struct v4l2_buffer buffer = {};
    for (int i = 0; i < requ_buffers.count; i++) {
        memset(&buffer, 0, sizeof(buffer));

        buffer.index = i;
        buffer.type = requ_buffers.type;
        buffer.memory = requ_buffers.memory;

        if (ioctl(_file, VIDIOC_QUERYBUF, &buffer) != 0) {
            perror("Querying buffers");
            return -1;
        }

        if (buffer.type != type) {
            perror("Type of buffer");
            return -1;
        }

        buffers[i].start = mmap(NULL, buffer.length, PROT_READ | PROT_WRITE, MAP_SHARED, _file, buffer.m.offset);
        buffers[i].length = buffer.length;

        if (MAP_FAILED == buffers[i].start) {
            /* If you do not exit here you should unmap() and free() the buffers mapped so far. */
            perror("Mapping memory with mmap");
            return -1;
        }
    }

    return 0;
}

void uninitialize_buffers(int _file) {
    for (int i = 0; i < requ_buffers.count; i++) {
        munmap(buffers[i].start, buffers[i].length);
    }

    free(buffers);
}

int start_stream(int _file) {
    struct v4l2_buffer buffer;
    for (int i = 0; i < requ_buffers.count; i++) {
        memset(&buffer, 0, sizeof(buffer));

        buffer.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        buffer.memory = V4L2_MEMORY_MMAP;
        buffer.index = i;

        if (-1 == xioctl(_file, VIDIOC_QBUF, &buffer)) {
            perror("VIDIOC_QBUF");
        }
    }

    if (-1 == xioctl(_file, VIDIOC_STREAMON, &type)) {
        perror("VIDIOC_STREAMON");
    }
}

int stop_stream(int _file) {
    if (-1 == xioctl(_file, VIDIOC_STREAMOFF, &type)) {
        perror("VIDIOC_STREAMOFF");
        return -1;
    }

    return 0;
}

double get_image_real_time(struct timespec real_time, struct timespec time1, struct timeval time0) {
    //printf("Cam: %0d.%6d \n", time0.tv_sec, time0.tv_usec);
    //printf("Monotone: %0d.%9d \n", time1.tv_sec, time1.tv_nsec);
    return real_time.tv_sec - time1.tv_sec + time0.tv_sec + 1e-9 * (real_time.tv_nsec - time1.tv_nsec) + 1e-6 * time0.tv_usec;
}

struct timespec monotonic_time, real_time;
double image_real_time;
char image_filename[200];

void save_image(struct v4l2_buffer buffer) {
    memset(image_filename, 0, sizeof(image_filename));
    clock_gettime(CLOCK_MONOTONIC, &monotonic_time);
    clock_gettime(CLOCK_REALTIME, &real_time);

    image_real_time = get_image_real_time(real_time, monotonic_time, buffer.timestamp);
    get_filename_d(image_filename, IMAGE_DIR, image_real_time, IMAGE_EXT);
    
    FILE *_temp_file = fopen(image_filename, "wb");
    fwrite(buffers[buffer.index].start, buffer.bytesused, 1, _temp_file);
    fflush(_temp_file);
    fclose(_temp_file);
    
    //printf("Received IMAGE with timestamp   : %f (size=%d bytes)\n", image_real_time, buffer.bytesused);

    compute_NPS_camera();
    
}

void *main_camera(void *params) {
    if (!USE_CAMERA)
        return NULL;

    int _file = open_file();

    /* display device information */
    display_available_inputs(_file);
    display_device_information(_file);
    display_available_formats(_file);

    /* set format, framerate */
    set_format_to_default(_file);
    set_framerate_to_default(_file);

    /* check format, framerate */
    display_device_crop_capabilities(_file);

    /* request buffers */
    request_buffers(_file);
    /* initialize and map buffers */
    initialize_buffers(_file);
    /* queuing buffers and start stream */
    start_stream(_file);

    count_images = 0;
    struct v4l2_buffer buffer;
    time_t start_data = time(NULL);
    while (time(NULL)- start_data < 60 * DURATION) {
        /* get buffer from ready queue */
        memset(&buffer, 0, sizeof(buffer));
        buffer.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        buffer.memory = V4L2_MEMORY_MMAP;

        if (xioctl(_file, VIDIOC_DQBUF, &buffer) == -1) {
            perror("Dequeuing buffer");
        }

        camera_ready = 1;
        //printf("Camera is ready !\n");
        if (wait_for_camera_and_radar() != 0) {
            return NULL;
        }

        /* save buffer content */
        if (SAVE_CAMERA && start_recording)
            save_image(buffer);

        /* put buffer in the queue */
        if (xioctl(_file, VIDIOC_QBUF, &buffer) == -1) {
            perror("Queuing buffer");
	    break;
        }

        count_images++;
    }

    /* stop stream */
    stop_stream(_file);

    /* unmap and uninitialize buffers */
    uninitialize_buffers(_file);
    printf("Camera finished\n");

    camera_running = 0;

    close(_file);
}
