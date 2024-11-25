import asyncio
from bleak import BleakScanner, BleakClient
import logging

from config import UUID

class BLEServiceScanner:
    def __init__(self):
        self.discovered_devices = []
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def detection_callback(self, device, advertisement_data):
        """Callback for when a device is detected during scanning"""
        if device not in self.discovered_devices:
            self.discovered_devices.append(device)
            self.logger.info(f"Found device: {device.name} ({device.address})")

    async def scan_and_read(self, scan_duration=10):
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
                self.logger.info(f"\nConnecting to device: {device.name} ({device.address})")
                async with BleakClient(device) as client:
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
                        for char in target_service.characteristics:
                            if "read" in char.properties:
                                try:
                                    value = await client.read_gatt_char(char.uuid)
                                    self.logger.info(f"Characteristic {char.uuid}: {value}")
                                except Exception as e:
                                    self.logger.error(f"Error reading characteristic {char.uuid}: {str(e)}")
                    else:
                        self.logger.warning("Target service not found on device")
                        
            except Exception as e:
                self.logger.error(f"Error connecting to device: {str(e)}")


async def client():
    scanner = BLEServiceScanner()
    await scanner.scan_and_read()


if __name__ == "__main__":
    asyncio.run(client())
