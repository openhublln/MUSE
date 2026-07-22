#include "lidar.h"


int start_lidar(void)
{
    pid_t pid;

    /* Put LiDAR into sampling mode */
    if (system("/home/openhub/MUSE/lidar/build/control "
               "/home/openhub/MUSE/lidar/config.json start") != 0)
    {
        return -1;
    }

    lidar_ready = 1;
    printf("Lidar ready\n");

    if (wait_for_camera_and_radar() != 0)
    {
        return -1;
    }

    pid = fork();

    if (pid < 0)
    {
        perror("fork");
        return -1;
    }

    if (pid == 0)
    {
        execl("/home/openhub/MUSE/lidar/build/acquisition",
              "acquisition",
              "/home/openhub/MUSE/lidar/config.json",
              "20",
              LIDAR_DIR,
              (char *)NULL);

        perror("execl");
        _exit(EXIT_FAILURE);
    }

    lidar_pid = pid;

    return 0;
}

int stop_lidar(void)
{
    if (lidar_pid <= 0)
    {
        return -1;
    }

    kill(lidar_pid, SIGTERM);

    waitpid(lidar_pid, NULL, 0);

    if (system("/home/openhub/MUSE/lidar/build/control "
               "/home/openhub/MUSE/lidar/config.json stop") != 0)
    {
        return -1;
    }

    lidar_ready = 0;
    lidar_pid = -1;

    return 0;
}


void *main_lidar(void *params)
{
    if (!USE_LIDAR)
        return NULL;

    if (start_lidar() != 0)
        return NULL;


    printf("Waiting for camera and radar...\n");
    if (synchronize_end_acquisition() == 0)
    {
        stop_lidar();
        printf("Stopping lidar...\n");
    }

    return NULL;
}