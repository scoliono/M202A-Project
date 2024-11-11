import os
import socket
from hostp2pd import HostP2pD

def start_go():
    """
    Starts the Group Owner (GO) mode for Wi-Fi Direct.
    """
    print("Starting Wi-Fi Direct Group Owner...")
    with HostP2pD(
        config_file="/etc/hostp2pd.yaml", 
        interface="p2p-dev-wlan0", 
        pin="12345670"
    ) as hostp2pd:
        print("Group Owner started. Waiting for connections...")
        while True:
            pass  # Keeps the group running

def send_file(filename, port=9000):
    """
    Sends a file to the connected client.
    """
    go_ip = "192.168.49.1"  # Default GO IP address for Wi-Fi Direct
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((go_ip, port))
        s.listen(1)
        print(f"Waiting for connection on {go_ip}:{port}...")
        conn, addr = s.accept()
        print(f"Connection from {addr}")
        with open(filename, 'rb') as f:
            while (chunk := f.read(1024)):
                conn.sendall(chunk)
        print("File sent successfully.")
        conn.close()

if __name__ == "__main__":
    filename = "random_file"  # Replace with your file
    start_go()  # Start GO mode
    send_file(filename)  # Send the file
