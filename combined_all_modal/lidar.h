#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include "utils.h"
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <signal.h>
#include <time.h>

#ifndef LIDAR_H
#define LIDAR_H


void *main_lidar(void *params);

int start_lidar(void);

int stop_lidar(void);
static pid_t lidar_pid = -1;

#endif