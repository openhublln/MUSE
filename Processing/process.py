from collections import defaultdict
import os
import numpy as np
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.animation import FFMpegWriter
from cfar import CA_CFAR
from tracking import Tracking
from sklearn.cluster import DBSCAN, HDBSCAN
from scipy.interpolate import UnivariateSpline
from ultralytics import YOLO
from utils import load_files, find_closest_index
from radar_processing import compute_rd

# ==========================================
# PATHS
# ==========================================

folder_path = f"./2026_05_20_13_30_38/"
save_video = True

output_video = f"./video.mp4"
dir_raw = Path(f"{folder_path}/radar")
dir_camera = Path(f"{folder_path}/camera")
background = np.load(f"./background_db.npy")
background_puissance = np.load(f"./background_puissance.npy")
save_path = Path("/linux/grotsartdehe/MUSE/")

# ==========================================
# RADAR PARAMETERS - DO NOT MODIFY THIS
# ==========================================

c = 3e8
fc = 24.125e9
lam = c / fc
BW = 554e6
N = 256
clk = 38461538
delay = 2214

delta_v = (lam * clk * 3.6) / (2 * N * (12 * (N + 4) + delay))
Vmax = delta_v * (N // 2)

range_bins = np.arange(N) * (c / (2 * BW))
velocity_bins = np.arange(N) * delta_v - Vmax

p_noise = 10 ** (82.03/10)  # noise power calibrated in anechoic chamber

# ==========================================
# LOAD FILES + TIMESTAMPS
# ==========================================

raw_files, raw_times = load_files(dir_raw, ".raw")
cam_files, cam_times = load_files(dir_camera, ".jpeg")
camera_cache = {
    f: np.array(Image.open(f))
    for f in cam_files
}
model = YOLO("yolo26n.pt")
CMAP = plt.get_cmap("tab20")

class ViewerController:
    def __init__(self):
        self.paused = False
        self.quit = False

    def on_key(self, event):
        if event.key == "p":
            self.paused = not self.paused
            print("Paused" if self.paused else "Resuming")

        elif event.key == "q":
            print("Quitting...")
            self.quit = True
            plt.close(event.canvas.figure)
            
            
def tracking_and_clustering(save_path, start_frame, end_frame):
    # To be changed according to the object we want to track.
    # Micro-Doppler signatures of pedestrians are typically weaker than those of vehicles.
    cfar_fonction = CA_CFAR(win_param=(15,20,9,10), threshold=12, rd_size=(N, N))
    
    # eps : The maximum distance between two samples for one to be considered as in the neighborhood of the other.
    # min_samples : The number of samples (or total weight) in a neighborhood for a point to be considered as a core point. This includes the point itself.
    dbscan = DBSCAN(eps=2, min_samples=3)
    tracks = Tracking()

    fig, (ax_rd, ax_cluster, ax_track, ax_cam) = plt.subplots(1, 4, figsize=(24, 6))
    
    ax_rd.set_xlim(velocity_bins[0], velocity_bins[-1])
    ax_rd.set_ylim(range_bins[0], range_bins[-1])
    ax_rd.set_xlabel("Velocity (km/h)")
    ax_rd.set_ylabel("Range (m)")
    
    ax_cluster.set_xlim(velocity_bins[0], velocity_bins[-1])
    ax_cluster.set_ylim(range_bins[0], range_bins[-1])
    ax_cluster.set_xlabel("Velocity (km/h)")
    ax_cluster.set_ylabel("Range (m)")
    
    im_rd = ax_rd.imshow(
        np.zeros((N, N)),
        extent=[velocity_bins[0], velocity_bins[-1],
                range_bins[0], range_bins[-1]],
        origin="lower",
        cmap="gray_r",
        aspect="auto",
        vmin=0,
        vmax=30
    )

    im_cluster = ax_cluster.imshow(
        np.zeros((N, N)),
        extent=[velocity_bins[0], velocity_bins[-1],
                range_bins[0], range_bins[-1]],
        origin="lower",
        cmap="gray_r",
        aspect="auto",
        vmin=0,
        vmax=1
    )

    im_cam = ax_cam.imshow(
        np.zeros((100, 100, 3), dtype=np.uint8)
    )
    controller = ViewerController()
    fig.canvas.mpl_connect(
        "key_press_event",
        controller.on_key
    )
    def on_close(event):
        controller.quit = True

    fig.canvas.mpl_connect("close_event", on_close)
    plt.ion()
    plt.show()

    for i in range(start_frame, end_frame):

        if controller.quit:
            break
    
        while controller.paused and not controller.quit:
            plt.pause(0.05)
    
        if controller.quit:
            break
    
        print(f"Processing frame {i}/{len(raw_files)}")
        rd_power = compute_rd(raw_files[i], background=background_puissance, remove_background=True)
        rd_power_wo = compute_rd(raw_files[i], background=background_puissance, remove_background=False)

        peaks = cfar_fonction(rd_power)

        detected_bins = np.where(peaks > 0)
        dbscan.fit(np.array(detected_bins).T)
        labels = dbscan.labels_
        # peak_met : metric to compute value of the cluster, can be "mean" or "max"
        # use max for RCS computation
        clusters = tracks.extract_clusters(detected_bins, labels, rd_power_wo, peak_met="mean")
        tracks.step(clusters)
        display_clusters(fig, ax_rd, ax_cluster, ax_track, ax_cam, im_rd, im_cluster, im_cam, i, rd_power, peaks, clusters, tracks)
    plt.close(fig)
    return


def display_clusters(fig, ax_rd, ax_cluster, ax_track, ax_cam, im_rd, im_cluster, im_cam, i, rd_power, peaks, clusters, tracker):
    im_rd.set_data(10*np.log10(rd_power).T)
    im_cluster.set_data(peaks.T)

    for coll in list(ax_cluster.collections):
        coll.remove()
    render_clusters(ax_cluster, i, clusters, CMAP, title="DBSCAN")

    ax_rd.set_title(f"RD frame {i}")

    # ================= CAMERA =================
    t = raw_times[i]
    idx = find_closest_index(cam_times, t)
    img = camera_cache[cam_files[idx]]
    
    ax_cam.imshow(img)
    
    for patch in list(ax_cam.patches):
        patch.remove()
    
    for text in list(ax_cam.texts):
        text.remove()
    
    results = model.track(img, persist=True, tracker="bytetrack.yaml", verbose=False)
    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue
    
        for k in range(len(boxes)):
            x1, y1, x2, y2 = boxes.xyxy[k].cpu().numpy()
            cls = int(boxes.cls[k].cpu().numpy())
            conf = float(boxes.conf[k].cpu().numpy())
    
            track_id = None
            if boxes.id is not None:
                track_id = int(boxes.id[k].cpu().numpy())
    
            label = model.names[cls]
            rect = plt.Rectangle(
                (x1, y1),
                x2 - x1,
                y2 - y1,
                fill=False,
                linewidth=2,
                edgecolor="lime",
                zorder=10   
            )
            ax_cam.add_patch(rect)
    
            ax_cam.text(
                x1,
                y1 - 5,
                f"{label} ID:{track_id} {conf:.2f}",
                color="white",
                bbox=dict(facecolor="black", alpha=0.6, edgecolor="none"),
                zorder=10
            )
    
    ax_cam.axis("off")
    ax_cam.set_title("Camera image")
    
    # ================= TRAJECTORIES =================
    ax_track.clear()

    tracks = tracker.get_confirmed_tracks()
    
    
    for tr in tracks:
    
        color = CMAP(tr.track_id % CMAP.N)
    
        ranges = []
        velocities = []
    
        for r_bin, d_bin in tr.centroid_history:
    
            r_bin = int(np.clip(round(r_bin), 0, N-1))
            d_bin = int(np.clip(round(d_bin), 0, N-1))
    
            ranges.append(
                range_bins[r_bin]
            )
    
            velocities.append(
                velocity_bins[d_bin]
            )
    
        if len(ranges) < 2:
            continue
    
        ax_track.plot(
            velocities,
            ranges,
            '-',
            color=color,
            linewidth=2
        )
    
        ax_track.scatter(
            velocities[-1],
            ranges[-1],
            color=color,
            s=80
        )
    
        ax_track.text(
            velocities[-1],
            ranges[-1],
            f"ID {tr.track_id}",
            color=color,
            fontsize=10,
            fontweight="bold"
        )
    
    ax_track.set_xlim(
        velocity_bins[0],
        velocity_bins[-1]
    )
    
    ax_track.set_ylim(
        range_bins[0],
        range_bins[-1]
    )
    
    ax_track.set_xlabel("Velocity (km/h)")
    ax_track.set_ylabel("Range (m)")
    ax_track.set_title("Range-Doppler Track History")
    ax_track.grid(True, alpha=0.3)
    
    fig.canvas.draw_idle()
    fig.canvas.flush_events()
    plt.pause(0.01)

def render_clusters(ax_pc, i, clusters, cmap, title="SNR"):
    for c in clusters:
        track_id = c.get("track_id", -1)
        color = cmap(track_id % cmap.N) if track_id >= 0 else "red"

        xs = []
        ys = []
        if "points" in c:
            
            for (d_bin, r_bin) in c["points"]:
            
                d_bin = int(np.clip(round(d_bin), 0, N-1))
                r_bin = int(np.clip(round(r_bin), 0, N-1))
            
                xs.append(
                    velocity_bins[d_bin]
                )
            
                ys.append(
                    range_bins[r_bin]
                )
        ax_pc.scatter(xs,ys,c=[color],s=5,marker="s",alpha=0.6)
        r_bin, d_bin = c["centroid"]
        d_bin = int(np.clip(round(d_bin), 0, N - 1))
        r_bin = int(np.clip(round(r_bin), 0, N - 1))
        ax_pc.scatter(
            velocity_bins[d_bin], range_bins[r_bin],
            c=[color], s=80, marker="x", linewidths=2
        )
    ax_pc.set_title(f"Clusters frame - {title} {i}")


# ==========================================
# MAIN
# ==========================================
def main():
    try:
        tracking_and_clustering(save_path, 100, 600)
    except KeyboardInterrupt:
        print("Interrupted by user")
        plt.close("all")
    
if __name__ == "__main__":
    main()

