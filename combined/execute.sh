clear
echo "compiling the script"
gcc -std=gnu99 -pthread -o main main.c utils.c camera.c radar.c && (echo "executing the script" ; ./main /DATA/TEST)