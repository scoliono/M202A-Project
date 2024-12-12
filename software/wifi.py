import dbus
import time
import subprocess

def connect_to_wifi(ssid: str, password: str):
    print(f"[connect_to_wifi] Connecting to Wi-Fi network: {ssid}")


    # Connect to NetworkManager's D-Bus service
    bus = dbus.SystemBus()
    nm = bus.get_object("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager")
    nm_props = dbus.Interface(nm, "org.freedesktop.DBus.Properties")
    nm_manager = dbus.Interface(nm, "org.freedesktop.NetworkManager")

    # Get all available devices
    devices = nm_manager.GetDevices()
    wifi_device = None

    # Find the Wi-Fi device
    for device_path in devices:
        device = bus.get_object("org.freedesktop.NetworkManager", device_path)
        device_props = dbus.Interface(device, "org.freedesktop.DBus.Properties")
        device_type = device_props.Get("org.freedesktop.NetworkManager.Device", "DeviceType")
        # DeviceType 2 is Wi-Fi
        if device_type == 2:
            wifi_device = device
            break

    if not wifi_device:
        print("No Wi-Fi device found.")
        return False
    else:
        print(f"Found Wi-Fi device at: {wifi_device.object_path}")

    print("[connect_to_wifi] Rescanning Wi-Fi networks...")
    try:
        subprocess.run(["nmcli", "dev", "wifi", "rescan"], check=True, timeout=10)
        print("[connect_to_wifi] Wi-Fi scan completed.")
    except subprocess.CalledProcessError as e:
        print(f"[connect_to_wifi] Wi-Fi scan failed: {e}")
        return False

    print("[connect_to_wifi] Proceeding with network setup...")


    # Create a new Wi-Fi connection
    wifi_props = dbus.Interface(wifi_device, "org.freedesktop.DBus.Properties")
    active_ap = wifi_props.Get("org.freedesktop.NetworkManager.Device.Wireless", "ActiveAccessPoint")

    # Disconnect from the current network if already connected
    # Check if a Wi-Fi connection is currently active
    if active_ap and active_ap != "/":
        try:
            nm_manager.DeactivateConnection(active_ap)
            print("[connect_to_wifi] Deactivated the current active connection.")
        except dbus.exceptions.DBusException as e:
            print(f"[connect_to_wifi] Failed to deactivate connection: {e}")
    else:
        print("[connect_to_wifi] No active connection to deactivate.")

    # Connection settings
    connection = {
        '802-11-wireless': {
            'ssid': dbus.ByteArray(ssid.encode('utf-8')),
            'mode': 'infrastructure',
        },
        '802-11-wireless-security': {
            'key-mgmt': 'wpa-psk',
            'psk': password,
        },
        'connection': {
            'id': ssid,
            'type': '802-11-wireless',
        },
        'ipv4': {
            'method': 'auto',
        },
        'ipv6': {
            'method': 'auto',
        }
    }

    # Add and activate the connection
    settings = bus.get_object("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager/Settings")
    settings_iface = dbus.Interface(settings, "org.freedesktop.NetworkManager.Settings")
    connection_path = settings_iface.AddConnection(connection)
    conn = bus.get_object("org.freedesktop.NetworkManager", connection_path)
    conn_iface = dbus.Interface(conn, "org.freedesktop.NetworkManager.Connection.Active")

    # Activate the connection
    active_connection = nm_manager.ActivateConnection(
        connection_path,  # Connection path
        wifi_device.object_path,  # Device path
        "/"
    )

    print(f"Connecting to SSID: {ssid}")
    time.sleep(5)  # Allow some time for connection
    state = nm_props.Get("org.freedesktop.NetworkManager", "State")

    # Check the connection state
    if state == 70:  # NM_STATE_CONNECTED_GLOBAL
        print("Connected successfully!")
        return True
    else:
        print("Failed to connect.")
        return False
