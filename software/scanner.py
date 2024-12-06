import asyncio
import json
import logging
from bleak import BleakScanner, BleakClient
from typing import Callable, Dict, List, Optional

from config import *
from sync import *


class BLEServiceScanner:
    def __init__(self, ssid: str, manifest: dict, packages: Optional[Dict[str, Package]] = {}, on_manifest: Optional[Callable] = None):
        self.discovered_devices = []
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.packages: Dict[str, Package] = packages
        self.peers: Dict[str, List[str]] = {}   # MAC address and what packages each peer has
        self.ssid = ssid                        # hostname for wifi
        self.manifest = manifest                # Our manifest
        self.on_manifest = on_manifest          # Callback for processing manifest

    def detection_callback(self, device, advertisement_data):
        """Callback for when a device is detected during scanning"""
        if device not in self.discovered_devices:
            self.discovered_devices.append(device)
            self.logger.info(f"Found device: {device.name} ({device.address})")

    async def connection_callback(self, client):
        """Callback for when a device is paired"""
        self.logger.info(f"Reading characteristics for service")

        try:
            # Retrieve the GATT services
            services = await client.get_services()

            # Find the handle for the desired characteristic UUID
            manifest_write_handle = None
            for service in services:
                for char in service.characteristics:
                    if char.uuid == PKG_MANIFEST_W:
                        manifest_write_handle = char.handle
                        break
                if manifest_write_handle:
                    break

            if not manifest_write_handle:
                self.logger.error(f"Characteristic with UUID {PKG_MANIFEST_W} not found.")
                return

            # Prepare data to write
            our_data = {
                "ssid": self.ssid,
                "manifest": self.manifest,
            }
            our_data_str = json.dumps(our_data)

            # Write to the characteristic using the handle
            await client.write_gatt_char(manifest_write_handle, our_data_str.encode('utf-8'), response=False)
            self.logger.info(f"Sent our package manifest using handle {manifest_write_handle}")

            # Proceed to read other characteristics or perform additional tasks

        except Exception as e:
            self.logger.error(f"Failed to interact with characteristics: {str(e)}")


    async def scan_and_read(self, manifest: dict, scan_duration=15):
        """Scan for devices and read characteristics of matching ones"""
        self.logger.info(f"Scanning for devices with service UUID: {UUID}")
        
        # Start scanning with callback
        scanner = BleakScanner(detection_callback=self.detection_callback, service_uuids=[UUID])
        await scanner.start()
        await asyncio.sleep(scan_duration)
        await scanner.stop()
        
        # Process discovered devices
        for device in self.discovered_devices:
            self.logger.info(device)
            try:
                self.logger.info(f"Connecting to device: {device.name} ({device.address}) ({device.rssi})")
                async with BleakClient(device) as client:
                    await self.connection_callback(client)
            except Exception as e:
                self.logger.error(f"Error connecting to device: {str(e)}")
