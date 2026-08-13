#include "lidar.h"

int init_lidar(void)
{
    if (system("/home/openhub/MUSE/lidar/build/control "
               "/home/openhub/MUSE/lidar/config.json start") != 0)
        return -1;

    print_time("control done");

    lidar_control_done = 1;

    while (USE_RADAR && !radar_initialisation)
        usleep(5000);

    return 0;
}

void *wait_lidar_ready(void *arg)
{
    int fd = *(int *)arg;
    free(arg);

    char c;

    if (read(fd, &c, 1) == 1)
    {
        print_time("LiDAR READY received");
        lidar_ready = 1;
    }

    close(fd);

    return NULL;
}


int start_lidar(void)
{
    pid_t pid; 
    /* Le LiDAR est prêt, on attend les autres capteurs */

    int ready_pipefd[2];
    int go_pipefd[2];

    pipe(ready_pipefd);
    pipe(go_pipefd);

    pid = fork();

    if (pid < 0)
    {
        perror("fork");
        return -1;
    }

    /* ---------- Child : lance acquisition ---------- */
    if (pid == 0)
    {
        close(ready_pipefd[0]);
        close(go_pipefd[1]);

        char ready_fd[16];
        char go_fd[16];

        snprintf(ready_fd, sizeof(ready_fd), "%d", ready_pipefd[1]);
        snprintf(go_fd, sizeof(go_fd), "%d", go_pipefd[0]);  

        execl(
            "/home/openhub/MUSE/lidar/build/acquisition",
            "acquisition",
            "/home/openhub/MUSE/lidar/config.json",
            "14",
            LIDAR_DIR,
            ready_fd,
            go_fd,
            (char *)NULL);

        perror("execl");
        _exit(EXIT_FAILURE);
    }

    /* ---------- Parent ---------- */
    close(ready_pipefd[1]);
    close(go_pipefd[0]);

    pthread_t wait_thread;

    int *fd = malloc(sizeof(int));
    *fd = ready_pipefd[0];

    pthread_create(
        &wait_thread,
        NULL,
        wait_lidar_ready,
        fd);

    pthread_detach(wait_thread);

    if (wait_for_camera_and_radar() != 0)
        return -1;

    char go = 'G';
    write(go_pipefd[1], &go, 1);
    close(go_pipefd[1]);
    print_time("GO envoyé"); 

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
    print_time("Lidar thread started");
    if (!USE_LIDAR){
        return NULL;
    }

    if (init_lidar() != 0)
        return NULL;

    if (start_lidar() != 0)
        return NULL;

    time_t start = time(NULL);

    while (time(NULL) - start < 60 * DURATION)
    {
        usleep(100000);
    }

    printf("Stopping lidar...\n");
    stop_lidar();
    printf("Lidar stopped.\n");

    return NULL;
}
