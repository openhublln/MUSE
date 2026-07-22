#ifndef RADAR
#define RADAR

#include <netdb.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>
#include <pthread.h>

#include "utils.h"

#define CODE_ADDR "192.168.16.2"
#define CODE_PORT 6171
#define QUEUE_SIZE 3

typedef enum flag {READY, NOT_READY} flag;

typedef struct MsgFromLoopback {
  flag  flag;
  char  type[5];
  int   length;
  char  content[800000];
  struct timeval timestamp;
} MsgFromLoopback;

int connect_to_code(void);
void exchange_clocks(void);
void write_to_code(char *buffer, int length);
void read_from_code(char *buffer, int length);
void get_msg_from_code(MsgFromLoopback *msg);
int send_ready(void);
void save_frame(MsgFromLoopback *msg);
void swap(int *m, int *n);
int get_next_writing_index(int writing_index);
int get_next_reading_index(int reading_index);
void *main_save(void *params);
void *main_radar(void *params);

#endif
