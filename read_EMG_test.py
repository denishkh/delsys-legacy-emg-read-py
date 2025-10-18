import socket
import struct
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import numpy as np
import csv
from datetime import datetime

# -----------------------------
# Configuration
# -----------------------------
TCU_HOST = "127.0.0.1"
EMG_PORT = 50041
IMU_PORT = 50042
BUFFER_SIZE = 8192
MAX_POINTS = 200

NUM_EMG = 16
NUM_IMU = 16

EMG_CHANNELS = [3, 5]   # list of EMG channels to plot (0-indexed)
IMU_CHANNELS = [3, 5]   # list of IMU channels to plot

EMG_Y_RANGE = (-0.0001, 0.0001)
IMU_Y_RANGE = (-2, 2)

# -----------------------------
# Buffers
# -----------------------------
emg_buffers = {ch: deque([0]*MAX_POINTS, maxlen=MAX_POINTS) for ch in EMG_CHANNELS}
imu_buffers = {ch: {'x': deque([0]*MAX_POINTS, maxlen=MAX_POINTS),
                    'y': deque([0]*MAX_POINTS, maxlen=MAX_POINTS),
                    'z': deque([0]*MAX_POINTS, maxlen=MAX_POINTS)}
               for ch in IMU_CHANNELS}

# -----------------------------
# Connect sockets
# -----------------------------
emg_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
emg_sock.connect((TCU_HOST, EMG_PORT))
emg_sock.setblocking(False)
print(f"Connected to EMG port {EMG_PORT}")

imu_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
imu_sock.connect((TCU_HOST, IMU_PORT))
imu_sock.setblocking(False)
print(f"Connected to IMU port {IMU_PORT}")

# -----------------------------
# Setup plots
# -----------------------------
fig, axes = plt.subplots(len(EMG_CHANNELS) + len(IMU_CHANNELS), 1, figsize=(10, 6))
if len(EMG_CHANNELS) + len(IMU_CHANNELS) == 1:
    axes = [axes]

# EMG plot lines
emg_lines = {}
for i, ch in enumerate(EMG_CHANNELS):
    ax = axes[i]
    line, = ax.plot([], [], lw=2, label=f'EMG {ch+1}')
    ax.set_ylim(*EMG_Y_RANGE)
    ax.set_xlim(0, MAX_POINTS)
    ax.set_title(f'EMG Channel {ch+1}')
    ax.set_xlabel('Samples')
    ax.set_ylabel('Amplitude')
    emg_lines[ch] = line
    ax.legend()

# IMU plot lines
imu_lines = {}
for i, ch in enumerate(IMU_CHANNELS):
    ax = axes[len(EMG_CHANNELS) + i]
    line_x, = ax.plot([], [], lw=2, color='b', label='X')
    line_y, = ax.plot([], [], lw=2, color='g', label='Y')
    line_z, = ax.plot([], [], lw=2, color='m', label='Z')
    ax.set_ylim(*IMU_Y_RANGE)
    ax.set_xlim(0, MAX_POINTS)
    ax.set_title(f'IMU Channel {ch+1}')
    ax.set_xlabel('Samples')
    ax.set_ylabel('Acceleration')
    ax.legend()
    imu_lines[ch] = {'x': line_x, 'y': line_y, 'z': line_z}

plt.tight_layout()

# -----------------------------
# CSV Logging
# -----------------------------
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_file = open(f"emg_imu_data_{timestamp}.csv", "w", newline="")
csv_writer = csv.writer(csv_file)
header = ['time'] + [f'EMG_{ch+1}' for ch in EMG_CHANNELS] + \
         [f'IMU_{ch+1}_X' for ch in IMU_CHANNELS] + \
         [f'IMU_{ch+1}_Y' for ch in IMU_CHANNELS] + \
         [f'IMU_{ch+1}_Z' for ch in IMU_CHANNELS]
csv_writer.writerow(header)

# -----------------------------
# Update function
# -----------------------------
def update(frame):
    # --- EMG ---
    emg_values = {ch: [] for ch in EMG_CHANNELS}
    try:
        while True:
            data = emg_sock.recv(BUFFER_SIZE)
            if not data:
                break
            samples = struct.unpack('<' + 'f'*(len(data)//4), data)
            arr = np.array(samples)
            if len(arr) % NUM_EMG == 0:
                arr = arr.reshape(-1, NUM_EMG)
                for ch in EMG_CHANNELS:
                    emg_values[ch].extend(arr[:, ch])
    except BlockingIOError:
        pass

    for ch in EMG_CHANNELS:
        if emg_values[ch]:
            avg_emg = np.mean(emg_values[ch][-int(len(emg_values[ch])/4):]) if len(emg_values[ch]) > 4 else emg_values[ch][-1]
            emg_buffers[ch].append(avg_emg)
            emg_lines[ch].set_data(range(len(emg_buffers[ch])), list(emg_buffers[ch]))

    # --- IMU ---
    try:
        data = imu_sock.recv(BUFFER_SIZE)
        if data:
            samples = struct.unpack('<' + 'f'*(len(data)//4), data)
            arr = np.array(samples)
            if len(arr) % (NUM_IMU * 3) == 0:
                arr = arr.reshape(-1, NUM_IMU, 3)
                latest = arr[-1]
                for ch in IMU_CHANNELS:
                    x, y, z = latest[ch]
                    imu_buffers[ch]['x'].append(x)
                    imu_buffers[ch]['y'].append(y)
                    imu_buffers[ch]['z'].append(z)
                    imu_lines[ch]['x'].set_data(range(len(imu_buffers[ch]['x'])), list(imu_buffers[ch]['x']))
                    imu_lines[ch]['y'].set_data(range(len(imu_buffers[ch]['y'])), list(imu_buffers[ch]['y']))
                    imu_lines[ch]['z'].set_data(range(len(imu_buffers[ch]['z'])), list(imu_buffers[ch]['z']))
    except BlockingIOError:
        pass

    # --- Save to CSV ---
    row = [datetime.now().strftime("%H:%M:%S.%f")]
    for ch in EMG_CHANNELS:
        row.append(emg_buffers[ch][-1])
    for ch in IMU_CHANNELS:
        row.extend([imu_buffers[ch]['x'][-1], imu_buffers[ch]['y'][-1], imu_buffers[ch]['z'][-1]])
    csv_writer.writerow(row)

    return list(emg_lines.values()) + [v for d in imu_lines.values() for v in d.values()]

# -----------------------------
# Animate
# -----------------------------
ani = animation.FuncAnimation(fig, update, interval=50, blit=False)
plt.show()

# -----------------------------
# Cleanup
# -----------------------------
emg_sock.close()
imu_sock.close()
csv_file.close()
