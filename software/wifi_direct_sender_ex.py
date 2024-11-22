import os
import socket
import subprocess
import time


def remove_existing_groups():
    """
    Removes any existing P2P groups to avoid conflicts.
    """
    print("Checking for existing P2P groups...")
    try:
        result = subprocess.run(["sudo", "wpa_cli", "-i", "p2p-dev-wlan0", "p2p_group_remove", "p2p-wlan0-0"], capture_output=True, text=True)
        if result.returncode == 0:
            print("Existing P2P group removed successfully.")
        else:
            print(f"No existing P2P group to remove or failed to remove: {result.stderr}")
    except Exception as e:
        print(f"Error removing existing P2P group: {e}")


def create_p2p_group():
    """
    Creates a P2P group using wpa_cli and returns the P2P interface name.
    """
    print("Creating P2P group...")
    result = subprocess.run(["sudo", "wpa_cli", "-i", "p2p-dev-wlan0", "p2p_group_add"], capture_output=True, text=True)
    if result.returncode == 0 and "P2P-GROUP-STARTED" in result.stdout:
        print(result.stdout)
        # Extract the P2P interface name from the output
        for line in result.stdout.splitlines():
            if "P2P-GROUP-STARTED" in line:
                interface = line.split()[1]  # Second field is the interface
                print(f"P2P group created on interface: {interface}")
                return interface
    print(f"Failed to create P2P group: {result.stderr}")
    return None


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


def wait_for_client(interface, timeout=None):
    """
    Waits for a client to connect to the Wi-Fi Direct group.
    If timeout is None, it waits indefinitely.
    """
    print(f"Waiting for a client to connect to {interface}...")
    start_time = time.time()
    while True:
        try:
            result = subprocess.run(
                ["iw", interface, "station", "dump"],
                capture_output=True,
                text=True,
            )
            if result.stdout.strip():
                print("Client connected.")
                return True
        except Exception as e:
            print(f"Error checking for client connection: {e}")
        time.sleep(1)

        if timeout and (time.time() - start_time) > timeout:
            print(f"No client connected after {timeout} seconds.")
            return False


def send_file(filename, port=9000):
    """
    Sends a file to the connected client.
    """
    go_ip = "192.168.49.1"
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
        # Remove any existing P2P groups
        remove_existing_groups()

        # Create P2P group and get the P2P interface name
        p2p_interface = create_p2p_group()
        if not p2p_interface:
            print("Failed to create P2P group. Exiting.")
            exit(1)

        # Configure IP for P2P interface
        configure_ip(p2p_interface, "192.168.49.1")

        # Wait for a client to connect
        if not wait_for_client(p2p_interface, timeout=None):
            print("No client connected. Exiting.")
            exit(1)

        # Send file once a client is connected
        send_file(filename)

    finally:
        print("Script finished.")
