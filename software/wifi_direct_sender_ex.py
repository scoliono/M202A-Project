import os
import socket
import subprocess
import threading
import time
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

def configure_ip(interface, ip, netmask="255.255.255.0"):
    """
    Manually configures the IP address on the interface.
    """
    print(f"Configuring IP {ip} on {interface}...")
    result = subprocess.run(
        ["sudo", "ifconfig", interface, ip, "netmask", netmask, "up"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"IP {ip} configured successfully on {interface}.")
    else:
        print(f"Failed to configure IP: {result.stderr}")

def wait_for_ip(interface, ip, timeout=10):
    """
    Waits for the specified IP to be assigned to the interface.
    """
    print(f"Waiting for IP {ip} to be assigned to {interface}...")
    start_time = time.time()
    while True:
        try:
            result = subprocess.run(
                ["ip", "addr", "show", interface],
                capture_output=True,
                text=True,
            )
            if ip in result.stdout:
                print(f"IP {ip} assigned to {interface}.")
                return True
        except Exception as e:
            print(f"Error checking IP: {e}")
        time.sleep(1)

        if (time.time() - start_time) > timeout:
            print(f"Timeout waiting for IP {ip} on {interface}.")
            return False

def wait_for_client(interface, timeout=None):
    """
    Waits for a client to connect to the Wi-Fi Direct group.
    If timeout is None, it waits indefinitely.
    """
    print(f"Waiting for a client to connect to {interface}...")
    start_time = time.time()
    while True:
        try:
            # Check the number of associated clients
            result = subprocess.run(
                ["iw", interface, "station", "dump"],
                capture_output=True,
                text=True,
            )
            if result.stdout.strip():  # If there is any output, a client is connected
                print("Client connected.")
                return True
        except Exception as e:
            print(f"Error checking for client connection: {e}")
        time.sleep(1)

        # Check for timeout if specified
        if timeout and (time.time() - start_time) > timeout:
            print(f"No client connected after {timeout} seconds.")
            return False

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

if __name__ == "__main__":
    filename = "random_file"  # Replace with your file
    try:
        stop_wifi()  # Stop Wi-Fi before enabling Wi-Fi Direct

        # Start Wi-Fi Direct Group Owner mode in a separate thread
        go_thread = threading.Thread(target=start_go, daemon=True)
        go_thread.start()

        # Wait briefly to ensure the Group Owner mode is initialized
        time.sleep(5)

        # Configure IP for Wi-Fi Direct interface
        configure_ip("p2p-dev-wlan0", "192.168.49.1")

        # Wait for the IP to be assigned
        if not wait_for_ip("p2p-dev-wlan0", "192.168.49.1"):
            print("Failed to configure the IP. Exiting.")
            exit(1)

        # Wait for a client to connect (indefinitely or with timeout)
        if not wait_for_client("p2p-dev-wlan0", timeout=None):  # Set timeout=None to wait forever
            print("No client connected. Exiting.")
            exit(1)

        # Send file once a client is connected
        send_file(filename)
    finally:
        start_wifi()  # Re-enable Wi-Fi after the script finishes
