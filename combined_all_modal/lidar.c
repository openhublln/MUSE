#include "lidar.h"

void *wait_lidar_start_recording(void *arg)
{
    int fd = *(int *)arg;
    free(arg);
    char c;

    if (read(fd, &c, 1) == 1)
    {
        printf("First LiDAR packet received.\n");
        start_recording = 1;
    }

    close(fd);

    return NULL;
}

int start_lidar(void)
{
    pid_t pid;
    int pipefd[2];

    if (pipe(pipefd) == -1)
    {
        perror("pipe");
        return -1;
    }

    /* Put LiDAR into sampling mode */
    if (system("/home/openhub/MUSE/lidar/build/control "
               "/home/openhub/MUSE/lidar/config.json start") != 0)
    {
        close(pipefd[0]);
        close(pipefd[1]);
        return -1;
    }

    lidar_ready = 1;
    printf("Lidar ready\n");

    if (wait_for_camera_and_radar() != 0)
    {
        close(pipefd[0]);
        close(pipefd[1]);
        return -1;
    }

    pid = fork();

    if (pid < 0)
    {
        perror("fork");
        close(pipefd[0]);
        close(pipefd[1]);
        return -1;
    }

    /* ---------- Child : lance acquisition ---------- */
    if (pid == 0)
    {
        /* Le fils n'utilise pas l'extrémité de lecture */
        close(pipefd[0]);

        char pipe_fd_str[16];
        snprintf(pipe_fd_str, sizeof(pipe_fd_str), "%d", pipefd[1]);

        execl(
            "/home/openhub/MUSE/lidar/build/acquisition",
            "acquisition",
            "/home/openhub/MUSE/lidar/config.json",
            "20",
            LIDAR_DIR,
            pipe_fd_str,
            (char *)NULL);

        /* Si on arrive ici, execl a échoué */
        perror("execl");
        close(pipefd[1]);
        _exit(EXIT_FAILURE);
    }

    /* ---------- Parent ---------- */

    /* Le parent n'écrit jamais dans le pipe */
    close(pipefd[1]);

    pthread_t wait_thread;

    int *fd = malloc(sizeof(int));
    if (fd == NULL)
    {
        perror("malloc");
        close(pipefd[0]);
        return -1;
    }

    *fd = pipefd[0];

    if (pthread_create(
            &wait_thread,
            NULL,
            wait_lidar_start_recording,
            fd) != 0)
    {
        perror("pthread_create");
        close(pipefd[0]);
        free(fd);
        return -1;
    }

    pthread_detach(wait_thread);

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