import socket
import subprocess

def connect_to_go(peer_mac):
    """
    Connects to the Group Owner (GO) using the peer's MAC address.
    """
    print(f"Connecting to GO with MAC address {peer_mac}...")
    try:
        # Initiate connection using the peer MAC address and PBC method
        subprocess.run(
            ["sudo", "wpa_cli", "-i", "p2p-dev-wlan0", "p2p_connect", peer_mac, "pbc"],
            check=True
        )
        print("Connected to Group Owner.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to connect to GO: {e}")
        raise

def receive_file(filename, port=9000):
    """
    Receives a file from the Group Owner.
    """
    go_ip = "192.168.49.1"  # Default GO IP address for Wi-Fi Direct
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((go_ip, port))
        print(f"Connected to {go_ip}:{port}")
        with open(filename, 'wb') as f:
            while True:
                data = s.recv(1024)
                if not data:
                    break
                f.write(data)
        print(f"File {filename} received successfully.")

if __name__ == "__main__":
    peer_mac = "2c:cf:67:9d:38:68"  # Replace with the GO's MAC address
    filename = "random_file"  # File to save as

    connect_to_go(peer_mac)  # Connect to the GO
    receive_file(filename)  # Receive the file
