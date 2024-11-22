import os
import socket
import subprocess
import threading
from hostp2pd import HostP2pD

def stop_wifi():
    """
    Disables the Wi-Fi interface to enable Wi-Fi Direct.
    """
    print("Disabling Wi-Fi to enable Wi-Fi Direct...")
    result = subprocess.run(["sudo", "ifconfig", "wlan0", "down"], capture_output=True, text=True)
    if result.returncode == 0:
        print("Wi-Fi disabled successfully.")
    else:
        print(f"Failed to disable Wi-Fi: {result.stderr}")

def start_go():
    """
    Starts the Group Owner (GO) mode for Wi-Fi Direct.
    """
    print("Starting Wi-Fi Direct Group Owner...")
    try:
        with HostP2pD(
            config_file="/etc/hostp2pd.yaml",  # Ensure this file is correctly configured
            interface="p2p-dev-wlan0",        # Adjust interface if necessary
            pin="12345670"                    # Optional PIN for pairing
        ) as hostp2pd:
            print("Group Owner started. Waiting for connections...")
            while True:
                pass  # Keeps the Group Owner running
    except Exception as e:
        print(f"Error starting Wi-Fi Direct: {e}")

def send_file(filename, port=9000):
    """
    Sends a file to the connected client.
    """
    go_ip = "192.168.49.1"  # Default Group Owner IP for Wi-Fi Direct
    print(f"Attempting to send file '{filename}' on {go_ip}:{port}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((go_ip, port))
            s.listen(1)
            print(f"Waiting for connection on {go_ip}:{port}...")
            conn, addr = s.accept()
            print(f"Connection established with {addr}")
            with open(filename, 'rb') as f:
                while (chunk := f.read(1024)):
                    conn.sendall(chunk)
            print("File sent successfully.")
            conn.close()
    except Exception as e:
        print(f"Error sending file: {e}")

def start_wifi():
    """
    Re-enables Wi-Fi after the script finishes.
    """
    print("Re-enabling Wi-Fi...")
    result = subprocess.run(["sudo", "ifconfig", "wlan0", "up"], capture_output=True, text=True)
    if result.returncode == 0:
        print("Wi-Fi re-enabled successfully.")
    else:
        print(f"Failed to re-enable Wi-Fi: {result.stderr}")

if __name__ == "__main__":
    filename = "random_file"  # Replace with the actual file path

    try:
        stop_wifi()  # Stop Wi-Fi before enabling Wi-Fi Direct

        # Start Wi-Fi Direct Group Owner mode in a separate thread
        go_thread = threading.Thread(target=start_go, daemon=True)
        go_thread.start()

        # Wait briefly to ensure the Group Owner mode is initialized
        import time
        time.sleep(5)

        # Send file in the main thread
        send_file(filename)
    finally:
        start_wifi()  # Re-enable Wi-Fi after the script finishes
