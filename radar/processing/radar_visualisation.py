from typing import List
import h5py
from matplotlib import pyplot as plt
import numpy as np


def load_rfft_data(filename: str) -> List[dict]:
        """Load RFFT data from an HDF5 file."""
        rfft_data = []
        with h5py.File(filename, "r") as f:
            for timestamp in f.keys():
                for data in f[timestamp].keys():
                    if data.startswith("rfft_"):
                        dataset = f[timestamp][data]
                        entry = {
                            "spectrum_db": dataset["spectrum_db"][()],
                            "threshold_db": dataset["threshold_db"][()],
                            }
                    rfft_data.append(entry)
        return rfft_data

def load_radc_data(filename: str) -> List[dict]:
        """Load RADC data from an HDF5 file."""
        radc_data = []
        with h5py.File(filename, "r") as f:
            sorted_timestamps = sorted(f.keys(), key=lambda x: int(x) if x.isdigit() else x)
            for timestamp in sorted_timestamps:
                
                for data in f[timestamp].keys():
                    if data.startswith("radc_"):
                        dataset = f[timestamp][data]
                        entry = {
                            "if1_freq_a_i": dataset["if1_freq_a_i"][()],
                            "if1_freq_a_q": dataset["if1_freq_a_q"][()],
                            "if2_freq_a_i": dataset["if2_freq_a_i"][()],
                            "if2_freq_a_q": dataset["if2_freq_a_q"][()],
                            "if1_freq_b_i": dataset["if1_freq_b_i"][()],
                            "if1_freq_b_q": dataset["if1_freq_b_q"][()],
                            }
                    radc_data.append(entry)
        return radc_data
    
    
# Don't work yet   
def compute_range_doppler_map(radc_batch: List[dict]) -> np.ndarray:
    """
    Compute a sparse Range-Doppler Map (Speed vs Distance) for FSK Radar.
    """
    N = 512             # FFT points
    c = 3e8             # Speed of light
    delta_f = 2e6   
    
    num_range_bins = 200
    num_doppler_bins = N
    rd_map = np.zeros((num_range_bins, num_doppler_bins))

    for frame in radc_batch:
        sigA = frame["if1_freq_a_i"] + 1j * frame["if1_freq_a_q"]
        sigB = frame["if1_freq_b_i"] + 1j * frame["if1_freq_b_q"]

        sigA = sigA - np.mean(sigA)
        sigB = sigB - np.mean(sigB)

        fftA = np.fft.fftshift(np.fft.fft(sigA, n=N))
        fftB = np.fft.fftshift(np.fft.fft(sigB, n=N))

        magnitude = np.abs(fftA)

        noise_floor = np.median(magnitude)
        threshold = noise_floor * 4.0 
        
        peaks = np.where(magnitude > threshold)[0]

        if len(peaks) > 0:
            phase_diff = fftB[peaks] * np.conj(fftA[peaks])
            angle = np.angle(phase_diff)
        
            angle = np.where(angle < 0, angle + 2 * np.pi, angle)
            distances = (c * angle) / (4 * np.pi * delta_f)

            for i, p_idx in enumerate(peaks):
                dist = distances[i]
                mag = magnitude[p_idx]
                if 0 < dist < 200:
                    r_bin = int((dist / 200.0) * num_range_bins)
                    if 0 <= r_bin < num_range_bins:
                        rd_map[r_bin, p_idx] = max(rd_map[r_bin, p_idx], mag)

    return rd_map
    
if __name__ == "__main__":
    import argparse

    # parser = argparse.ArgumentParser(description="Radar Data Visualisation")
    # parser.add_argument(
    #     "--file", required=True, help="Path to the HDF5 file containing radar data"
    # )
    # args = parser.parse_args()
    max_velocity = 100  # Maximum velocity in km/h
    max_range = 200  # Maximum range in meters
    radc_data = load_radc_data("/home/samuel/Documents/MUSE/radar/measurements/measurements_2_radc.hdf5")
    
    BATCH_SIZE = 256
    STEP = 16
    
    batch_0 = radc_data[0:BATCH_SIZE]
    range_doppler_map = compute_range_doppler_map(batch_0)
    num_doppler_bins = range_doppler_map.shape[1]
    num_range_bins = range_doppler_map.shape[0]
    
     # Create the velocity and range bins
    velocity_bins = np.linspace(-max_velocity, max_velocity, num_doppler_bins)
    range_bins = np.linspace(0, max_range, num_range_bins)
    
    plt.ion()
    fig, ax = plt.subplots(figsize=(10, 6))

    
    im = ax.imshow(range_doppler_map, 
                   aspect='auto', 
                   origin='lower',
                   extent=[velocity_bins.min(), velocity_bins.max(), range_bins.min(), range_bins.max()],
                   cmap='jet')

    plt.colorbar(im, label='Amplitude (dB)')
    ax.set_xlabel('Vitesse (km/h)')
    ax.set_ylabel('Distance (m)')
    title = ax.set_title('Range-Doppler Map - Frame 0')
    
    plt.show(block=False)

    try:
        for t in range(0, len(radc_data) - BATCH_SIZE, STEP):
            batch = radc_data[t : t + BATCH_SIZE]
            
            rd_map= compute_range_doppler_map(batch)
            
            im.set_data(rd_map)
            title.set_text(f'Range-Doppler Map - Index {t}/{len(radc_data)}')
            plt.pause(0.01)
    except KeyboardInterrupt:
        print("Animation arrêtée par l'utilisateur.")

    plt.ioff()
    plt.show()