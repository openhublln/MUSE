#ifndef MAIN
#define MAIN

#define _GNU_SOURCE

#include <stdio.h>
#include <pthread.h>
#include <sys/stat.h>

#include "utils.h"
#include "camera.h"
#include "radar.h"
#include "lidar.h"

int main(int argc, char *argv[]);

#endif