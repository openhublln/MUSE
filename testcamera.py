import cv2
import os
from datetime import datetime
import time

# 获取脚本目录
script_dir = os.path.dirname(os.path.abspath(__file__))

# 定义固定的保存路径
save_path_rgba = os.path.join(script_dir, "DATA", "camera_rgba")

# 创建保存目录（如果不存在）
os.makedirs(save_path_rgba, exist_ok=True)

def capture_and_save_frames(save_path_rgba):
    # 打开摄像头
    cap = cv2.VideoCapture(0)

    # 检查摄像头是否成功打开
    if not cap.isOpened():
        print("错误: 无法打开摄像头。")
        return

    # 获取帧的宽度和高度（根据需要调整）
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 设置帧率
    fps = 30

    # 获取初始的 CLOCK_MONOTONIC 和 CLOCK_REALTIME 时间
    monotonic_start = time.clock_gettime(time.CLOCK_MONOTONIC)
    realtime_start = time.time()  # 获取系统当前时间

    # 记录程序开始时间
    start_time = time.time()

    # 运行时间限制（秒）
    run_duration = 500 * 60  # 5分钟

    run_continuously = 1

    # 开始捕捉和保存帧
    try:
        while True:
            # 检查运行时间是否超过限制
            current_time = time.time()
            elapsed_time = current_time - start_time
            '''
            if elapsed_time > run_duration:
                print("已达到运行时间限制，程序终止。")
                break
            '''
            if run_continuously < 0:
                break
            
            # 从摄像头读取一帧
            ret, frame = cap.read()
            if not ret:
                print("错误: 无法读取帧。")
                break

            # 获取当前的 CLOCK_MONOTONIC 和 CLOCK_REALTIME 时间
            clock_monotonic = time.clock_gettime(time.CLOCK_MONOTONIC)
            clock_realtime = time.time()

            # 获取缓冲区时间戳
            buffertimestamp = clock_monotonic - monotonic_start

            # 计算当前帧的绝对时间戳
            timestamp = realtime_start + buffertimestamp
            timestamp_datetime = datetime.fromtimestamp(timestamp)

            # 确保时间格式相同
            formatted_timestamp = timestamp_datetime.strftime('%Y-%m-%d_%H-%M-%S-%f')
            formatted_clock_realtime = datetime.fromtimestamp(clock_realtime).strftime('%Y-%m-%d_%H-%M-%S-%f')
            formatted_clock_monotonic = datetime.fromtimestamp(clock_monotonic).strftime('%Y-%m-%d_%H-%M-%S-%f')
            formatted_buffertimestamp = datetime.fromtimestamp(buffertimestamp).strftime('%Y-%m-%d_%H-%M-%S-%f')

            # 打印 CLOCK_REALTIME, CLOCK_MONOTONIC 和 buffertimestamp 的值
            #print(f"CLOCK_REALTIME: {formatted_clock_realtime}")
            #print(f"CLOCK_MONOTONIC: {formatted_clock_monotonic}")
            #print(f"buffertimestamp: {formatted_buffertimestamp}")

            # 将帧转换为 RGBA
            frame_rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)

            # 保存为 RGBA 图像
            rgba_filename = f"{timestamp_datetime.strftime('%Y-%m-%d_%H-%M-%S-%f')}.png"
            rgba_file_path = os.path.join(save_path_rgba, rgba_filename)
            cv2.imwrite(rgba_file_path, frame_rgba)

            # 计算显示经过的时间
            display_elapsed_time = (datetime.now() - timestamp_datetime).total_seconds()

            # 等待以保持所需的 FPS
            if display_elapsed_time < 1.0 / fps:
                delay_ms = int((1.0 / fps - display_elapsed_time) * 1000)
                if delay_ms > 0:
                    cv2.waitKey(delay_ms)

            # 检查按键事件
            # 这里不再需要窗口展示，因此不需要 cv2.imshow 和 cv2.waitKey 的结合使用
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break

    except KeyboardInterrupt:
        print("用户中断。")

    finally:
        # 释放摄像头并关闭所有 OpenCV 窗口
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    capture_and_save_frames(save_path_rgba)

