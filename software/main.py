import asyncio
from advertiser import ble_server
from config import FILE_DIR
from file_server import FileTransferServer
from scanner import BLEServiceScanner
from enum import IntEnum
from sync import Package
from wifi import connect_to_wifi
import os
import socket  # To get the hostname
import time

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
    pkg = Package("my-package", 1, FILE_DIR)
    pkg.load_from_filesystem()
    our_manifest = pkg.load_manifest(FILE_DIR + "/manifest.json")

    packages = {
        "SamplePackage": pkg
    }

    # state machine
    state = State.STARTUP

    # peer's manifest, in order to compare chunk versions
    peer_manifest = {}
    peer_ssid = ""
    def on_manifest_received(metadata: dict):
        global state, peer_manifest
        state = State.BT_COMPLETE
        peer_manifest = metadata["manifest"]
        peer_ssid = metadata["ssid"]
        print('[main] Got package manifest + SSID')
    
    def on_wifi_finished(success: bool):
        global state
        if success:
            print('[main] Wifi transferring completed successfully.')
        else:
            print('[main] Wifi transfer failed! Going back to BT scan...')
        state = State.WIFI_COMPLETE
    
    # BLE + Wi-Fi services
    scanner = BLEServiceScanner(socket.gethostname(), packages, on_manifest=on_manifest_received)

    # arent these classes basically the same?
    wifi = FileTransferServer(pkg, callback=on_wifi_finished)

    while True:
        # switch between BT advertising and scanning every 5s
        # either function may call `on_manifest_received()` to exit this loop
        while state != State.BT_COMPLETE:
            state = State.BT_ADVERT
            await ble_server(packages, on_manifest_received)
            state = State.BT_SCAN
            await scanner.scan_and_read(our_manifest)

        # is there is no difference between manifests?
        if not pkg.manifests_differ(our_manifest, peer_manifest):
            # TODO: temp blacklist this peer
            continue

        # simplest way to agree on who is AP/who is client
        if our_manifest["ssid"] < peer_manifest["ssid"]:
            state = State.WIFI_AP
        else:
            state = State.WIFI_CLIENT

        # either start AP/connect to it
        if state == State.WIFI_AP:
            result = subprocess.run(["ap_mode.sh"], capture_output=True, text=True)
        elif state == State.WIFI_CLIENT:
            result = subprocess.run(["client_mode.sh"], capture_output=True, text=True)
            time.sleep(8)
            connect_to_wifi(peer_manifest["ssid"], "password")

        # get differing versions of chunks
        diff = pkg.get_missing_chunks(peer_manifest)

        # we know which chunks we need, now do WiFi transfer
        while state != State.WIFI_COMPLETE:
            if state == State.WIFI_AP:
                wifi.start_server(diff)
            elif state == State.WIFI_CLIENT:
                wifi.start_client(diff)

if __name__ == "__main__":
    asyncio.run(main())
