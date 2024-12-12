import subprocess

def connect_to_wifi(ssid: str, password: str):
    print(f"[connect_to_wifi] Connecting to Wi-Fi network: {ssid}")

    # Step 1: Rescan for Wi-Fi networks
    print("[connect_to_wifi] Rescanning Wi-Fi networks...")
    try:
        subprocess.run(["nmcli", "dev", "wifi", "rescan"], check=True, timeout=10, text=True)
        print("[connect_to_wifi] Wi-Fi scan completed.")
    except subprocess.CalledProcessError as e:
        print(f"[connect_to_wifi] Wi-Fi scan failed: {e.stderr}")
        return False

    # Step 2: Disconnect from any active network
    print("[connect_to_wifi] Checking for active connections...")
    try:
        active_connection = subprocess.run(
            ["nmcli", "-t", "-f", "active,ssid", "connection", "show"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        active_lines = active_connection.stdout.strip().split("\n")
        for line in active_lines:
            if line.startswith("yes:"):
                active_ssid = line.split(":")[1]
                print(f"[connect_to_wifi] Disconnecting from active network: {active_ssid}")
                subprocess.run(["nmcli", "connection", "down", active_ssid], check=True, text=True)
    except subprocess.CalledProcessError:
        print("[connect_to_wifi] No active connection to disconnect.")

    # Step 3: Connect to the specified Wi-Fi network
    print(f"[connect_to_wifi] Connecting to SSID: {ssid}...")
    try:
        result = subprocess.run(
            ["nmcli", "dev", "wifi", "connect", ssid, "password", password],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"[connect_to_wifi] Connected to {ssid}. Output:\n{result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[connect_to_wifi] Failed to connect to {ssid}. Error:\n{e.stderr}")
        return False
