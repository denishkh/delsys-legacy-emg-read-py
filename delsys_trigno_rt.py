#!/usr/bin/env python3
"""
Simple Delsys Trigno real-time example:
 - send text commands to command port (50040)
 - listen to EMG data port (50043) in real time and print raw packets

Caution:
 - TCU (Trigno Control Utility / SDK server) must be running on HOST.
 - This prints raw bytes from the data stream. Use Delsys SDK docs or example code
   to correctly parse packets into channel values.
"""

import socket
import threading
import time

HOST = "127.0.0.1"   # IP of machine running TCU (change if remote)
CMD_PORT = 50040     # Command port (send START, STOP, SENSOR n PAIR, ...)
EMG_PORT = 50043    # EMG data port (binary stream)
BUFFER_SIZE = 4096

def listen_data_port(host, port):
    """Connect to data port and print raw bytes as they arrive."""
    print(f"[listener] connecting to data port {host}:{port} ...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, port))
        print(f"[listener] connected to {host}:{port}")
        # Receive loop
        while True:
            data = s.recv(BUFFER_SIZE)
            if not data:
                print("[listener] connection closed by server")
                break
            # Print simple info + first bytes hex (avoid huge prints)
            print(f"[data recv] {len(data)} bytes. first 64 bytes (hex): {data[:64].hex()}")
            # TODO: parse according to Delsys packet spec (SDK docs) here
    except Exception as e:
        print(f"[listener] exception: {e}")
    finally:
        s.close()

def command_console(host, port):
    """Connect to the command port and allow interactive sending of text commands."""
    print(f"[cmd] connecting to command port {host}:{port} ...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, port))
        print(f"[cmd] connected to {host}:{port}")
        # optional: read initial replies from the command port
        s.settimeout(0.5)
        try:
            r = s.recv(1024)
            if r:
                print("[cmd] initial reply:", r.decode(errors='ignore'))
        except socket.timeout:
            pass

        while True:
            cmd = input("COMMAND (type 'exit' to quit): ").strip()
            if not cmd:
                continue
            if cmd.lower() in ("exit", "quit"):
                print("[cmd] closing command connection.")
                break
            # The TCU expects plain text commands like START, STOP, SENSOR 1 PAIR, etc.
            try:
                s.sendall((cmd + "\r\n").encode())   # CRLF is safe
                # read response (non-blocking with small timeout)
                s.settimeout(0.5)
                try:
                    resp = s.recv(4096)
                    if resp:
                        print("[cmd reply]", resp.decode(errors='ignore'))
                except socket.timeout:
                    # no immediate reply
                    pass
            except Exception as e:
                print("[cmd] send error:", e)
                break
    except Exception as e:
        print(f"[cmd] connection error: {e}")
    finally:
        s.close()

def main():
    # start listener thread (EMG data)
    listener_thread = threading.Thread(target=listen_data_port, args=(HOST, EMG_PORT), daemon=True)
    listener_thread.start()

    # run command console in main thread so user can type
    try:
        command_console(HOST, CMD_PORT)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        print("Exiting. (listener thread is daemon and will exit when program ends.)")

if __name__ == "__main__":
    main()
