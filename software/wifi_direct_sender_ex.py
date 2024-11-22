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


def disconnect_wifi():
    """
    Disconnects from the current Wi-Fi network to prepare for Wi-Fi Direct.
    """
    logging.info("Disconnecting from Wi-Fi network...")
    result = subprocess.run(["sudo", "wpa_cli", "-i", "wlan0", "disconnect"], capture_output=True, text=True)
    if result.returncode == 0:
        logging.info("Wi-Fi disconnected successfully.")
    else:
        logging.warning(f"Failed to disconnect Wi-Fi: {result.stderr}")


def verify_interface(interface):
    """
    Verifies if a given interface exists.
    """
    logging.info(f"Verifying interface {interface}...")
    result = subprocess.run(["iw", "dev"], capture_output=True, text=True)
    if interface in result.stdout:
        logging.info(f"Interface {interface} is available.")
        return True
    else:
        logging.error(f"Interface {interface} not found.")
        return False


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


def reconnect_to_wifi(ssid, password):
    """
    Reconnects to the specified Wi-Fi network.
    """
    logging.info(f"Reconnecting to Wi-Fi network '{ssid}'...")
    try:
        commands = [
            ["sudo", "wpa_cli", "-i", "wlan0", "add_network"],
            ["sudo", "wpa_cli", "-i", "wlan0", "set_network", "0", f'ssid="{ssid}"'],
            ["sudo", "wpa_cli", "-i", "wlan0", "set_network", "0", f'psk="{password}"'],
            ["sudo", "wpa_cli", "-i", "wlan0", "enable_network", "0"],
            ["sudo", "wpa_cli", "-i", "wlan0", "save_config"],
        ]
        for cmd in commands:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"Failed to execute command '{cmd}': {result.stderr}")
                return False
        logging.info("Reconnected to Wi-Fi successfully.")
        return True
    except Exception as e:
        logging.error(f"Error reconnecting to Wi-Fi: {e}")
        return False


if __name__ == "__main__":
    ssid = "SpectrumSetup-6B"
    password = "grainphone703"
    try:
        logging.info("Starting Wi-Fi Direct script...")

        # Disconnect Wi-Fi
        disconnect_wifi()

        # Verify p2p-dev-wlan0 exists
        if not verify_interface("p2p-dev-wlan0"):
            logging.error("P2P interface p2p-dev-wlan0 not found. Exiting.")
            exit(1)

        # Remove any existing P2P groups
        remove_existing_groups()

        # Create P2P group
        p2p_interface = create_p2p_group()
        if not p2p_interface:
            logging.error("Failed to create P2P group. Exiting.")
            exit(1)

        # Configure IP for P2P interface
        configure_ip(p2p_interface, "192.168.49.1")

    finally:
        # Reconnect to Wi-Fi
        reconnect_to_wifi(ssid, password)
        logging.info("Script finished.")
