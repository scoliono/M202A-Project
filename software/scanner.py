import asyncio
import json
import logging
from bleak import BleakScanner, BleakClient
from typing import Callable, Dict, List, Optional

from config import UUID, PKG_LIST_R, PKG_MANIFEST_R, PKG_REQUEST_W
from sync import *


class BLEServiceScanner:
    def __init__(self, packages: Optional[Dict[str, Package]] = {}, on_manifest: Optional[Callable] = None):
        self.discovered_devices = []
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.packages: Dict[str, Package] = packages
        self.peers: Dict[str, List[str]] = {}   # MAC address and what packages each peer has
        self.on_manifest = on_manifest          # Callback for processing manifest

    def detection_callback(self, device, advertisement_data):
        """Callback for when a device is detected during scanning"""
        if device not in self.discovered_devices:
            self.discovered_devices.append(device)
            self.logger.info(f"Found device: {device.name} ({device.address})")

    async def connection_callback(self, client):
        """Callback for when a device is paired"""
        # Get all services
        services = await client.get_services()
        
        # Find our target service
        target_service = None
        for service in services:
            if str(service.uuid).lower() == self.target_service_uuid.lower():
                target_service = service
                break
        
        if target_service:
            self.logger.info(f"Reading characteristics for service: {target_service.uuid}")
            
            try:
                pkg_list_raw = await client.read_gatt_char(PKG_LIST_R)
                pkg_list = json.loads(pkg_list_raw)
                self.logger.info(f"Got package list: {pkg_list_raw}")

                self.peers[pkg_list["mac"]] = pkg_list["pkgs"]
                for pkg_name in pkg_list["pkgs"]:
                    await client.write_gatt_char(PKG_REQUEST_W, pkg_name.encode('utf-8'))
                    pkg_manifest_raw = await client.read_gatt_char(PKG_MANIFEST_R)
                    self.logger.info(f"Got package manifest: {pkg_manifest_raw}")
                    pkg_manifest = json.loads(pkg_manifest_raw)

                    if pkg_name not in self.packages:
                        self.packages[pkg_name] = Package(name, 1)
                    self.on_manifest(pkg_manifest)

            except Exception as e:
                print("Failed to package list from characteristics", str(e))

        else:
            self.logger.warning("Target service not found on device")

    async def scan_and_read(self, scan_duration=5):
        """Scan for devices and read characteristics of matching ones"""
        self.logger.info(f"Scanning for devices with service UUID: {UUID}")
        
        # Start scanning with callback
        scanner = BleakScanner(detection_callback=self.detection_callback, service_uuids=[UUID])
        await scanner.start()
        await asyncio.sleep(scan_duration)
        await scanner.stop()
        
        # Process discovered devices
        for device in self.discovered_devices:
            try:
                self.logger.info(f"Connecting to device: {device.name} ({device.address})")
                async with BleakClient(device) as client:
                    await connection_callback(client)                        
            except Exception as e:
                self.logger.error(f"Error connecting to device: {str(e)}")
