import socket
import struct
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import numpy as np

# -----------------------------
# Configuration
# -----------------------------
TCU_HOST = "127.0.0.1"
EMG_PORT = 50041
IMU_PORT = 50042
BUFFER_SIZE = 8192  # larger buffer for high-rate EMG
MAX_POINTS = 200

NUM_EMG = 16
NUM_IMU = 16  # each has X, Y, Z

EMG_CHANNEL = 9   # EMG sensor index (0–15)
IMU_CHANNEL = 9   # IMU sensor index (0–15)

EMG_Y_RANGE = (-0.0001, 0.0001)
IMU_Y_RANGE = (-2, 2)

# -----------------------------
# Buffers
# -----------------------------
emg_buffer = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)
imu_x = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)
imu_y = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)
imu_z = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)

# -----------------------------
# Connect sockets
# -----------------------------
emg_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
emg_sock.connect((TCU_HOST, EMG_PORT))
emg_sock.setblocking(False)  # non-blocking read
print(f"Connected to EMG port {EMG_PORT}")

imu_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
imu_sock.connect((TCU_HOST, IMU_PORT))
imu_sock.setblocking(False)
print(f"Connected to IMU port {IMU_PORT}")

# -----------------------------
# Setup plots
# -----------------------------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))

# EMG
line_emg, = ax1.plot([], [], lw=2, color='r')
ax1.set_title(f'EMG Channel {EMG_CHANNEL + 1}')
ax1.set_xlabel('Samples')
ax1.set_ylabel('Amplitude')
ax1.set_ylim(*EMG_Y_RANGE)
ax1.set_xlim(0, MAX_POINTS)

# IMU
line_x, = ax2.plot([], [], lw=2, color='b', label='X')
line_y, = ax2.plot([], [], lw=2, color='g', label='Y')
line_z, = ax2.plot([], [], lw=2, color='m', label='Z')
ax2.set_title(f'IMU Channel {IMU_CHANNEL + 1}')
ax2.set_xlabel('Samples')
ax2.set_ylabel('Acceleration')
ax2.set_ylim(*IMU_Y_RANGE)
ax2.set_xlim(0, MAX_POINTS)
ax2.legend()

# -----------------------------
# Update Function
# -----------------------------
def update(frame):
    # --- EMG (fast, 2000 Hz) ---
    emg_values = []
    try:
        while True:  # read all available EMG data
            data = emg_sock.recv(BUFFER_SIZE)
            if not data:
                break
            samples = struct.unpack('<' + 'f'*(len(data)//4), data)
            arr = np.array(samples)
            if len(arr) % NUM_EMG == 0:
                arr = arr.reshape(-1, NUM_EMG)
                emg_values.extend(arr[:, EMG_CHANNEL])
    except BlockingIOError:
        pass  # no new data

    if emg_values:
        # Average recent EMG samples to reduce noise and update frequency
        avg_emg = np.mean(emg_values[-int(len(emg_values)/4):]) if len(emg_values) > 4 else emg_values[-1]
        emg_buffer.append(avg_emg)
        # print(f"EMG[{EMG_CHANNEL}] = {avg_emg:.6f}")

    # --- IMU (slow, 148 Hz) ---
    try:
        data = imu_sock.recv(BUFFER_SIZE)
        if data:
            samples = struct.unpack('<' + 'f'*(len(data)//4), data)
            arr = np.array(samples)
            if len(arr) % (NUM_IMU * 3) == 0:
                arr = arr.reshape(-1, NUM_IMU, 3)
                latest_vals = arr[-1][IMU_CHANNEL]
                x, y, z = latest_vals
                imu_x.append(x)
                imu_y.append(y)
                imu_z.append(z)
                # print(f"IMU[{IMU_CHANNEL}] = X:{x:.4f}, Y:{y:.4f}, Z:{z:.4f}")
    except BlockingIOError:
        pass

    # --- Update plots ---
    line_emg.set_data(range(len(emg_buffer)), list(emg_buffer))
    line_x.set_data(range(len(imu_x)), list(imu_x))
    line_y.set_data(range(len(imu_y)), list(imu_y))
    line_z.set_data(range(len(imu_z)), list(imu_z))

    return line_emg, line_x, line_y, line_z

# -----------------------------
# Animate
# -----------------------------
ani = animation.FuncAnimation(fig, update, interval=50, blit=False)
plt.tight_layout()
plt.show()

# -----------------------------
# Cleanup
# -----------------------------
emg_sock.close()
imu_sock.close()
