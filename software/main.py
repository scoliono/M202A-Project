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
    our_manifest = pkg.load_manifest(FILE_DIR + "/manifest.json")

    packages = {
        "SamplePackage": pkg
    }

    # state machine
    state = State.STARTUP

    # peer's manifest, in order to compare chunk versions
    peer_manifest = {}
    def on_manifest_received(manifest: dict):
        global state, peer_manifest
        state = State.BT_COMPLETE
        peer_manifest = manifest
        print('[main] Got package manifest')
    
    # BLE + Wi-Fi services
    scanner = BLEServiceScanner(packages, on_manifest=on_manifest_received)

    # arent these classes basically the same?
    wifi = FileTransferServer(pkg, callback=on_wifi_server_finished)

    def on_wifi_finished(success: bool):
        global state
        if success:
            print('[main] Wifi transferring completed successfully.')
        else:
            print('[main] Wifi transfer failed! Going back to BT scan...')
        state = State.WIFI_COMPLETE

    while True:
        # switch between BT advertising and scanning every 5s
        # either function may call `on_manifest_received()` to exit this loop
        while state != State.BT_COMPLETE:
            state = State.BT_ADVERT
            await ble_server(packages, on_manifest_received)
            state = State.BT_SCAN
            await scanner.scan_and_read(our_manifest)

        # TODO: either start AP/connect to it


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
