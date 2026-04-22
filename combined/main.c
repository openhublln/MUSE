#include "main.h"

int main(int argc, char *argv[]) {
    pthread_t thread_camera, thread_radar;

    if (argc < 2) {
        printf("Usage: %s <output_dir>\n", argv[0]);
        return 1;
    }

    char *output_dir = argv[1];

    snprintf(IMAGE_DIR, sizeof(IMAGE_DIR), "%s/camera/", output_dir);
    snprintf(FRAME_DIR, sizeof(FRAME_DIR), "%s/radar/", output_dir);

    printf("Camera dir: %s\n", IMAGE_DIR);
    printf("Radar dir : %s\n", FRAME_DIR);

    mkdir(output_dir, 0777);
    mkdir(IMAGE_DIR, 0777);
    mkdir(FRAME_DIR, 0777);

    init_variables();

    /* delete previous jpeg files */
    if (DELETE_OLD_DATA_FILES) {
        if (USE_CAMERA)
            delete_folder_jpeg_files(IMAGE_DIR);

        if (USE_RADAR)
            delete_folder_raw_files(FRAME_DIR);
    }

    pthread_create(&thread_camera, NULL, main_camera, NULL);
    pthread_create(&thread_radar, NULL, main_radar, NULL);

    /* set thread affinity for cores */
    cpu_set_t cpusetCamera, cpusetRadar;
    int res;

    CPU_ZERO(&cpusetCamera);
    CPU_SET(2, &cpusetCamera);
    printf("set camera thread core: %d\n",
        pthread_setaffinity_np(thread_camera, sizeof(cpusetCamera), &cpusetCamera));

    CPU_ZERO(&cpusetRadar);
    CPU_SET(2, &cpusetRadar);
    printf("set radar  thread core: %d\n",
        pthread_setaffinity_np(thread_radar, sizeof(cpusetRadar), &cpusetRadar));

    pthread_join(thread_camera, NULL);
    pthread_join(thread_radar, NULL);

    return 0;
}