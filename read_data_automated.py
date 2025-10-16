import socket

# -----------------------------
# Configuration
# -----------------------------
TCU_HOST = "127.0.0.1"
CMD_PORT = 50040

# -----------------------------
# Connect and claim MASTER
# -----------------------------
def main():
    try:
        cmd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cmd_sock.connect((TCU_HOST, CMD_PORT))
        print(f"[CMD] Connected to {TCU_HOST}:{CMD_PORT}")
    except Exception as e:
        print("[CMD] Connection failed:", e)
        return

    # Function to continuously receive and print replies
    def receive_replies(sock):
        buffer = b""
        while True:
            try:
                chunk = sock.recv(1024)
                if not chunk:
                    print("[CMD] Connection closed by TCU")
                    break
                buffer += chunk
                while b"\r\n" in buffer:
                    line, buffer = buffer.split(b"\r\n", 1)
                    text = line.decode(errors='ignore').strip()
                    if text:
                        print(f"[CMD Reply] {text}")
            except Exception as e:
                print("[CMD] Receive error:", e)
                break

    # Start reply listener thread
    import threading
    recv_thread = threading.Thread(target=receive_replies, args=(cmd_sock,), daemon=True)
    recv_thread.start()

    # Small delay to ensure listener thread is running
    import time
    time.sleep(0.2)

    # Send MASTER command
    cmd_sock.sendall(b"MASTER\r\n")
    print("[CMD] Sent: MASTER")

    # Optionally, test with other commands
    test_commands = [
        "SENSOR 1 PAIR",
        "SENSOR 1 ENABLE EMG",
        "SENSOR 1 ENABLE AUX",
        "START"
    ]

    for cmd in test_commands:
        cmd_sock.sendall((cmd + "\r\n").encode())
        print(f"[CMD] Sent: {cmd}")
        time.sleep(0.2)  # small delay between commands

    # Keep main thread alive to receive replies
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Exiting program...")

if __name__ == "__main__":
    main()
