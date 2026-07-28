#include "radar.h"

MsgFromLoopback *queue[QUEUE_SIZE];
int writing_index, reading_index;
int LAST_EDITED, OTHER_0, OTHER_1;
MsgFromLoopback *writing_msg, *reading_msg;
struct timeval radar_tv;
int code_socket;

int first_frame;
int first_min;
int connect_to_code(void) {
    struct hostent *loopback_server;
    struct sockaddr_in serv_addr;

    if ((code_socket = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        printf("[connect to code] socket not created\n");
        return -1;
    }

    if ((loopback_server = gethostbyname(CODE_ADDR)) == NULL) {
        printf("[connect to code] not connected to code\n");
        return -1;
    }

    memset((char *)&serv_addr, 0, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    bcopy((char *)loopback_server->h_addr, (char *)&serv_addr.sin_addr.s_addr, loopback_server->h_length);
    serv_addr.sin_port = htons(CODE_PORT);

    if (connect(code_socket, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        printf("[connect to code] error connecting\n");
	perror("[connect to code] error connecting\n");
        return -1;
    }

    printf("Connected to code.\n");
    return 0;
}

struct timeval t0;
void exchange_clocks(void) {
    struct timeval tvstart, tvstop, tvclock;
    char buffer[9] = {0};
    long int elapsed;
    int iter = 0, uslimit = 200;

    while (1) {
        gettimeofday(&tvstart, NULL);
        write_to_code("REQUEST_", 8);
        read(code_socket, buffer, 8);
        read(code_socket, &tvclock.tv_sec, 4);
        read(code_socket, &tvclock.tv_usec, 4);
        gettimeofday(&tvstop, NULL);

        elapsed = tvstop.tv_usec - tvstart.tv_usec + 1e6 * (tvstop.tv_sec - tvstart.tv_sec);
        printf("start : %0d.%06d\n", tvstart.tv_sec, tvstart.tv_usec);
        printf("stop  : %0d.%06d\n", tvstop.tv_sec, tvstop.tv_usec);
        printf("clock : %0d.%06d\n", tvclock.tv_sec, tvclock.tv_usec);
        printf("elapsed time [us] = %li\n", elapsed);

        if (elapsed < uslimit) {
            write_to_code("ACCEPTED", 8);
            t0.tv_usec = tvstart.tv_usec + elapsed / 2;
            t0.tv_sec = tvstart.tv_sec;

            printf("=> sent at : %0d.%06d\n", t0.tv_sec, t0.tv_usec);
            printf("=> clock   : %0d.%06d\n", tvclock.tv_sec, tvclock.tv_usec);

            t0.tv_usec -= tvclock.tv_usec;
            t0.tv_sec -= tvclock.tv_sec;

            printf("=> reference t0 : %0d.%06d\n", t0.tv_sec, t0.tv_usec);
            clock_correction(&t0);
            printf("=> reference t0 : %0d.%06d (corrected)\n", t0.tv_sec, t0.tv_usec);
            printf("=> with param. : iter=%d, uslimit=%d\n", iter, uslimit);
            break;
        }
        if (iter == 2000) {
            uslimit += 20;
            iter = 0;
        }
        iter++;
        usleep(100);
    }
}

void read_from_code(char *buffer, int length) {
    read(code_socket, buffer, length);
}

void write_to_code(char *buffer, int length) {
    write(code_socket, buffer, length);
}

void get_msg_from_code(MsgFromLoopback *msg) {
    int nbytes, position = 0;
    read(code_socket, msg->type, 4);
    read(code_socket, &msg->length, 4);

    read(code_socket, &msg->timestamp.tv_sec, 4);
    read(code_socket, &msg->timestamp.tv_usec, 4);

    while (position < msg->length) {
        nbytes = read(code_socket, &msg->content[position], msg->length - position);
        position += nbytes;
    }
    
    msg->timestamp.tv_sec += t0.tv_sec;
    msg->timestamp.tv_usec += t0.tv_usec;
    clock_correction(&msg->timestamp);
    radar_tv.tv_sec = msg->timestamp.tv_sec;
    radar_tv.tv_usec = msg->timestamp.tv_usec;
    /*
    struct timeval time_TCP;
    gettimeofday(&time_TCP, NULL);
    time_TCP.tv_sec -= msg->timestamp.tv_sec;
    time_TCP.tv_usec -= msg->timestamp.tv_usec;
    printf("TCP: %0d.%06d \n", time_TCP);
    */

}

int send_ready(void) {
    write(code_socket, "READY", 5);
}

double frame_real_time;
char frame_filename[200];
void save_frame(MsgFromLoopback *msg) {
    memset(frame_filename, 0, sizeof(frame_filename));

    get_filename_tv(frame_filename, FRAME_DIR, msg->timestamp, FRAME_EXT);
    
    FILE *_temp_file = fopen(frame_filename, "wb");
    fwrite(msg->content, msg->length, 1, _temp_file);
    fflush(_temp_file);
    fclose(_temp_file);

    //printf("Received [FRAME] with timestamp : %0d.%06d (size=%d bytes)\n", msg->timestamp.tv_sec, msg->timestamp.tv_usec, msg->length);
    
    compute_NPS_radar();
    
}

void swap(int *m, int *n) {
  int _temp = *m;
  *m = *n;
  *n = _temp;
}

int get_next_writing_index(int writing_index) {
  if (writing_index == OTHER_0) {
    swap(&LAST_EDITED, &OTHER_0);
  }
  else {
    swap(&LAST_EDITED, &OTHER_1);
  }

  //printf("LAST EDITED : %d\n", LAST_EDITED);
  //printf("OTHER_0     : %d\n", OTHER_0);
  //printf("OTHER_1     : %d\n", OTHER_1);

  if (OTHER_0 == reading_index) {
    return OTHER_1;
  }
  else {
    return OTHER_0;
  }
}

int get_next_reading_index(int reading_index) {
  if (queue[LAST_EDITED]->flag == READY) {
    return LAST_EDITED;
  }
  else {
    return -1;
  }
}

void *main_save(void *params) {
    while(1) {
        while ((reading_index = get_next_reading_index(reading_index)) == -1) {
            usleep(200);
        } //printf("next reading index : %d\n", reading_index);
        reading_msg = queue[reading_index];

        if (SAVE_RADAR)
            save_frame(reading_msg);

        reading_msg->flag = NOT_READY;
        //printf("Message saved from %d.\n", reading_index);
    }
}

double timeval_difference(struct timeval *cam, struct timeval *rad){
    int time_cam, time_rad;
    double time_diff;
    time_cam = cam->tv_sec * 1000000 + cam->tv_usec;
    time_rad = rad->tv_sec * 1000000 + rad->tv_usec;
    time_diff = (time_cam - time_rad) / 1000.0;
    /*
    if (time_diff < 0){
        time_diff = - time_diff;
    }
    */
    return time_diff;
}

struct timeval last_now, radar_t0, cam_t0, cam_tv;
double drift_t0, drift_t1, drift;
void *main_radar(void *params) {
    if (!USE_RADAR)
        return NULL;

    MsgFromLoopback msg0, msg1, msg2;
    queue[0] = &msg0;
    queue[1] = &msg1;
    queue[2] = &msg2;

    for(int i = 0; i < QUEUE_SIZE; i++) {
        queue[i]->flag = NOT_READY;
    }

    LAST_EDITED = 0;
    OTHER_0 = 1;
    OTHER_1 = 2;

    writing_index = OTHER_0;
    writing_msg = queue[writing_index];
    reading_index = LAST_EDITED;
    reading_msg = queue[reading_index];

    printf("write flag : %d\n", READY);
    printf("read  flag : %d\n", NOT_READY);
    for(int i = 0; i < QUEUE_SIZE; i++) {
        printf("buffer %d : flag = %d\n", i, queue[i]->flag);
    }
    
    connect_to_code();
    exchange_clocks();
    
    pthread_t save_thd;
    pthread_create(&save_thd, NULL, main_save, NULL);

    radar_ready = 1;
    first_frame = 1;
    first_min = 1;
    time_t t = time(NULL);
    struct tm *tm_info = localtime(&t);
    char filename[100];
    strftime(filename, sizeof(filename), "drift_%Y-%m-%d_%H-%M.csv", tm_info);
    FILE *fp = fopen(filename, "w");
    if (fp == NULL){
        perror("Error when opening csv file> \n");
    }
    time_t start = time(NULL);
    time_t last_sync = start;
    if (wait_for_camera_and_radar() != 0) {
        return NULL;
    }
    time_t start_data = time(NULL);
    while (time(NULL)- start_data < 60 * DURATION) {
        send_ready();
        gettimeofday(&last_now, NULL);
        get_msg_from_code(writing_msg);
        
        if (start_recording) {
            writing_msg->flag = READY;
            //save_frame(writing_msg);
        }


        writing_index = get_next_writing_index(writing_index);
        writing_msg = queue[writing_index];
        
        if (first_frame == 1){
            radar_t0.tv_sec = radar_tv.tv_sec;
            radar_t0.tv_usec = radar_tv.tv_usec;
            cam_t0.tv_sec = last_now.tv_sec;
            cam_t0.tv_usec = last_now.tv_usec;
            
            printf("Initial radar: %0d.%06d \n", radar_t0.tv_sec, radar_t0.tv_usec);
            printf("Initial camera: %0d.%06d \n", cam_t0.tv_sec, cam_t0.tv_usec);
            
            drift_t0 = timeval_difference(&cam_t0, &radar_t0);
            printf("Initial drift: %.3f [ms] \n", drift_t0);
            first_frame = 0;
        }

        time_t now_time = time(NULL);
        if (now_time - last_sync >= 120 && first_min == 1){
            gettimeofday(&cam_tv, NULL);
            printf("Current radar: %0d.%06d \n", radar_tv.tv_sec, radar_tv.tv_usec);
            printf("Current camera: %0d.%06d \n", cam_tv.tv_sec, cam_tv.tv_usec);
            drift_t1 = timeval_difference(&cam_tv, &radar_tv);
            printf("[%d min]: Drift=%.3f [ms] \n", (now_time - start) / 60, drift_t1);
            first_min = 0;
            last_sync = now_time;

        }

        if (now_time - last_sync >= 60 && first_min == 0){
            double drift_tv;
            gettimeofday(&cam_tv, NULL);
            printf("Current radar: %0d.%06d \n", radar_tv.tv_sec, radar_tv.tv_usec);
            printf("Current camera: %0d.%06d \n", cam_tv.tv_sec, cam_tv.tv_usec);
            drift_tv = timeval_difference(&cam_tv, &radar_tv);
            drift = drift_tv - drift_t1;
            if (drift < 0){
                drift = - drift;
            }
            printf("[%d min]: Drift=%.3f [ms] and current drift=%.3f [ms] \n", (now_time - start) / 60, drift, drift_tv);
            last_sync = now_time;
            fprintf(fp, "%.3f \n", drift);
        }

    }
    fclose(fp);
    printf("Radar finished\n");
    radar_running = 0;
    printf("CSV file closed successfully !\n");
}
