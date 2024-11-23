from hostp2pd import HostP2pD
import time
import subprocess
import sys

def disable_wifi():
    print("Disabling Wi-Fi on wlan0...")
    # Bring down wlan0 interface
    subprocess.run(["sudo", "ifconfig", "wlan0", "down"])
    # Stop wpa_supplicant or NetworkManager to prevent reconnection
    subprocess.run(["sudo", "systemctl", "stop", "wpa_supplicant"])
    # If you're using NetworkManager, uncomment the following line:
    subprocess.run(["sudo", "systemctl", "stop", "NetworkManager"])

def enable_wifi():
    print("Re-enabling Wi-Fi on wlan0...")
    # Bring up wlan0 interface
    subprocess.run(["sudo", "ifconfig", "wlan0", "up"])
    # Start wpa_supplicant or NetworkManager to reconnect
    subprocess.run(["sudo", "systemctl", "start", "wpa_supplicant"])
    # If you're using NetworkManager, uncomment the following line:
    subprocess.run(["sudo", "systemctl", "start", "NetworkManager"])

def check_and_remove_p2p_interface():
    # Check for existing p2p-wlan0-0 interface and remove it if exists
    print("Checking for existing P2P interfaces...")
    result = subprocess.run(["iw", "dev"], capture_output=True, text=True)
    if "p2p-wlan0-0" in result.stdout:
        print("Removing existing p2p-wlan0-0 interface")
        subprocess.run(["sudo", "iw", "dev", "p2p-wlan0-0", "del"])
    else:
        print("No existing P2P interfaces found.")

def main():
    try:
        # Disable Wi-Fi to free up the interface for P2P
        disable_wifi()
        # Remove existing P2P interfaces if any
        check_and_remove_p2p_interface()

        # Create an instance of HostP2pD
        hostp2pd = HostP2pD(
            config_file="hostp2pd.yaml",
            interface="p2p-dev-wlan0",
        )

        # Start hostp2pd in interactive mode
        with hostp2pd:
            print("hostp2pd is running, waiting for connections...")
            while True:
                time.sleep(10)
                # Optionally, print connected stations
                if hostp2pd.addr_register:
                    print("Connected Stations:")
                    for addr, name in hostp2pd.addr_register.items():
                        print(f"  {addr} - {name}")

    except KeyboardInterrupt:
        print("Exiting...")

    finally:
        # Re-enable Wi-Fi before exiting
        enable_wifi()
        print("Wi-Fi re-enabled.")

if __name__ == "__main__":
    main()