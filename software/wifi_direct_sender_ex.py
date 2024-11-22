import os
import socket
import subprocess
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("wifi_direct.log"),  # Logs to a file
        logging.StreamHandler()                 # Logs to the console
    ]
)

def stop_network_manager():
    """
    Stops NetworkManager to avoid conflicts with Wi-Fi Direct.
    """
    logging.info("Stopping NetworkManager...")
    result = subprocess.run(["sudo", "systemctl", "stop", "NetworkManager"], capture_output=True, text=True)
    if result.returncode == 0:
        logging.info("NetworkManager stopped successfully.")
    else:
        logging.warning(f"Failed to stop NetworkManager: {result.stderr}")


def restart_network_manager():
    """
    Restarts NetworkManager to restore normal network functionality.
    """
    logging.info("Restarting NetworkManager...")
    result = subprocess.run(["sudo", "systemctl", "start", "NetworkManager"], capture_output=True, text=True)
    if result.returncode == 0:
        logging.info("NetworkManager restarted successfully.")
    else:
        logging.warning(f"Failed to restart NetworkManager: {result.stderr}")


def remove_existing_groups():
    """
    Removes any existing P2P groups to avoid conflicts.
    """
    logging.info("Checking for existing P2P groups...")
    try:
        result = subprocess.run(["sudo", "wpa_cli", "-i", "p2p-dev-wlan0", "p2p_group_remove", "p2p-wlan0-0"],
                                capture_output=True, text=True)
        if result.returncode == 0:
            logging.info("Existing P2P group removed successfully.")
        else:
            logging.warning(f"No existing P2P group to remove or failed to remove: {result.stderr}")
    except Exception as e:
        logging.error(f"Error removing existing P2P group: {e}")


def create_p2p_group():
    """
    Creates a P2P group using wpa_cli and returns the P2P interface name.
    """
    logging.info("Creating P2P group...")
    result = subprocess.run(["sudo", "wpa_cli", "-i", "p2p-dev-wlan0", "p2p_group_add"], capture_output=True, text=True)
    if result.returncode == 0 and "P2P-GROUP-STARTED" in result.stdout:
        logging.info("P2P group creation successful.")
        logging.debug(result.stdout)
        # Extract the P2P interface name from the output
        for line in result.stdout.splitlines():
            if "P2P-GROUP-STARTED" in line:
                interface = line.split()[1]  # Extract the interface name
                logging.info(f"P2P group created on interface: {interface}")
                return interface
    logging.error(f"Failed to create P2P group: {result.stderr}")
    return None


def configure_ip(interface, ip, netmask="255.255.255.0"):
    """
    Manually configures the IP address on the interface.
    """
    logging.info(f"Configuring IP {ip} on {interface}...")
    result = subprocess.run(
        ["sudo", "ifconfig", interface, ip, "netmask", netmask, "up"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        logging.info(f"IP {ip} configured successfully on {interface}.")
    else:
        logging.error(f"Failed to configure IP: {result.stderr}")


def wait_for_client(interface, timeout=None):
    """
    Waits for a client to connect to the Wi-Fi Direct group.
    If timeout is None, it waits indefinitely.
    """
    logging.info(f"Waiting for a client to connect to {interface}...")
    start_time = time.time()
    while True:
        try:
            result = subprocess.run(
                ["iw", interface, "station", "dump"],
                capture_output=True,
                text=True,
            )
            if result.stdout.strip():  # A client is connected
                logging.info("Client connected.")
                return True
        except Exception as e:
            logging.error(f"Error checking for client connection: {e}")
        time.sleep(1)

        if timeout and (time.time() - start_time) > timeout:
            logging.warning(f"No client connected after {timeout} seconds.")
            return False


def send_file(filename, port=9000):
    """
    Sends a file to the connected client.
    """
    go_ip = "192.168.49.1"
    logging.info(f"Attempting to send file '{filename}' on {go_ip}:{port}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((go_ip, port))
            s.listen(1)
            logging.info(f"Waiting for connection on {go_ip}:{port}...")
            conn, addr = s.accept()
            logging.info(f"Connection established with {addr}")
            with open(filename, 'rb') as f:
                while (chunk := f.read(1024)):
                    conn.sendall(chunk)
            logging.info("File sent successfully.")
            conn.close()
    except Exception as e:
        logging.error(f"Error sending file: {e}")


if __name__ == "__main__":
    filename = "random_file"  # Replace with your file
    try:
        logging.info("Starting Wi-Fi Direct script...")

        # Stop NetworkManager to prevent conflicts
        stop_network_manager()

        # Remove any existing P2P groups
        remove_existing_groups()

        # Create P2P group and get the P2P interface name
        p2p_interface = create_p2p_group()
        if not p2p_interface:
            logging.error("Failed to create P2P group. Exiting.")
            exit(1)

        # Configure IP for P2P interface
        configure_ip(p2p_interface, "192.168.49.1")

        # Wait for a client to connect
        if not wait_for_client(p2p_interface, timeout=None):
            logging.warning("No client connected. Exiting.")
            exit(1)

        # Send file once a client is connected
        send_file(filename)

    finally:
        # Restart NetworkManager after Wi-Fi Direct is finished
        restart_network_manager()
        logging.info("Script finished.")
