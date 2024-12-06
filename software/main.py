import asyncio
from advertiser import ble_server
from config import FILE_DIR
from file_server import FileTransferServer
from scanner import BLEServiceScanner
from enum import IntEnum
from sync import Package
from wifi import connect_to_wifi
import os
import random
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
    
    manifest_path = FILE_DIR + '/manifest.json'
    if not os.path.exists(manifest_path):
        with open(manifest_path, 'w') as manifest_file:
            manifest_file.write('{"name":"my-package","version":1,"files":{}}')

    our_manifest = pkg.load_manifest(manifest_path)

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
    hostname = socket.gethostname()
    scanner = BLEServiceScanner(hostname, our_manifest, packages=packages, on_manifest=on_manifest_received)

    # arent these classes basically the same?
    wifi = FileTransferServer(pkg, callback=on_wifi_finished)

    while True:
        # switch between BT advertising and scanning every 5s
        # either function may call `on_manifest_received()` to exit this loop
        if int(hostname[-1]) > 2:
            state = State.BT_ADVERT
        else:
            state = State.BT_SCAN

        while state == State.BT_ADVERT or state == State.BT_SCAN:
            # hack: BT mode switching wasn't working
            if state == State.BT_ADVERT:
                await ble_server(packages, on_manifest_received)
            elif state == State.BT_SCAN:
                await scanner.scan_and_read(our_manifest)

        print('[main] Checking differences between manifests')
        # is there is no difference between manifests?
        if not pkg.manifests_differ(our_manifest, peer_manifest):
            print('[main] Manifests did not differ; starting over')
            # TODO: temp blacklist this peer
            continue

        # simplest way to agree on who is AP/who is client
        if our_manifest["ssid"] < peer_manifest["ssid"]:
            state = State.WIFI_AP
        else:
            state = State.WIFI_CLIENT

        # either start AP/connect to it
        if state == State.WIFI_AP:
            print('Choosing WiFi AP mode')
            result = subprocess.run(["ap_mode.sh"], capture_output=True, text=True)
        elif state == State.WIFI_CLIENT:
            print('Choosing WiFi client mode')
            result = subprocess.run(["client_mode.sh"], capture_output=True, text=True)
            await asyncio.sleep(5)
            print('Connecting to AP')
            connect_to_wifi(peer_manifest["ssid"], "password")

        # get differing versions of chunks
        print('Calculating missing chunks')
        diff = pkg.get_missing_chunks(peer_manifest)

        # we know which chunks we need, now do WiFi transfer
        while state != State.WIFI_COMPLETE:
            if state == State.WIFI_AP:
                print('Starting WiFi transmit - server')
                wifi.start_server(diff)
            elif state == State.WIFI_CLIENT:
                print('Starting WiFi transmit - client')
                wifi.start_client(diff)

if __name__ == "__main__":
    asyncio.run(main())
