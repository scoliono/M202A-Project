import asyncio
from advertiser import ble_server
from config import FLIE_DIR
from file_server import FileTransferServer
from scanner import BLEServiceScanner
from enum import IntEnum
from sync import Package
import os

class State(IntEnum):
    STARTUP = 0
    BT_ADVERT = 1
    BT_SCAN = 2
    BT_COMPLETE = 3
    WIFI_AP = 4
    WIFI_CLIENT = 5
    WIFI_COMPLETE = 6


async def main():
    # Initialize state of package and chunks
    pkg = Package("SamplePackage", 1, FILE_DIR)
    pkg.load_from_filesystem()

    packages = {
        "SamplePackage": pkg
    }

    # state machine
    state = State.STARTUP

    # BLE + Wi-Fi services
    scanner = BLEServiceScanner(packages, on_manifest=on_manifest_received)

    # arent these classes basically the same?
    wifi = FileTransferServer(pkg, callback=on_wifi_server_finished)

    # peer's manifest, in order to compare chunk versions
    peer_manifest = {}
    def on_manifest_received(manifest: dict):
        global state, peer_manifest
        state = State.BT_COMPLETE
        peer_manifest = manifest
        print('[main] Got package manifest')

    def on_wifi_finished(success: bool):
        global state
        if success:
            print('[main] Wifi transferring completed successfully.')
        else:
            print('[main] Wifi transfer failed! Going back to BT scan...')
        state = State.WIFI_COMPLETE

    while True:
        # switch between BT advertising and scanning every 5s
        while state != State.BT_COMPLETE:
            state = State.BT_ADVERT
            await ble_server(packages)
            state = State.BT_SCAN
            await scanner.scan_and_read()

        # TODO: either start AP/connect to it
        if state == State.WIFI_AP:
            result = subprocess.run(["ap_mode.sh"], capture_output=True, text=True)
        else if state == State.WIFI_CLIENT:
            result = subprocess.run(["client_mode.sh"], capture_output=True, text=True)
            ssid = other_name
            connect_to_wifi(ssid, "password")
        



        # get differing versions of chunks
        diff = pkg.get_missing_chunks(peer_manifest)

        # we know which chunks we need, now do WiFi transfer
        while state != State.WIFI_COMPLETE:
            if state == State.WIFI_AP:
                wifi.start_server()
            elif state == State.WIFI_CLIENT:
                wifi.start_client(diff)





def connect_to_wifi(ssid, password):
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

    # Create a new Wi-Fi connection
    wifi_props = dbus.Interface(wifi_device, "org.freedesktop.DBus.Properties")
    active_ap = wifi_props.Get("org.freedesktop.NetworkManager.Device.Wireless", "ActiveAccessPoint")

    # Disconnect from the current network if already connected
    if active_ap != "/":
        nm_manager.DeactivateConnection(active_ap)

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





if __name__ == "__main__":
    asyncio.run(main())
