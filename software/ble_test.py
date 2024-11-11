import asyncio
from multiprocessing import Process
from bluez_peripheral import get_message_bus, Advertisement
from bluez_peripheral.util import Adapter
from bluez_peripheral.gatt import Service, characteristic, CharacteristicFlags as CharFlags
from bluez_peripheral.agent import NoIoAgent
import struct
from bleak import BleakScanner


# Define a custom GATT Service
class CustomService(Service):
    def __init__(self):
        super().__init__("1234", True)  # Replace "1234" with your desired service UUID

    @characteristic("5678", CharFlags.READ | CharFlags.WRITE)
    def custom_characteristic(self, options):
        return b"Hello BLE!"  # Default value

    def write_custom_characteristic(self, value):
        # Handle writing to this characteristic
        print(f"Characteristic written: {value}")


# Function to handle BLE advertising
async def advertise():
    bus = await get_message_bus()

    service = CustomService()
    await service.register(bus)

    # Register pairing agent
    agent = NoIoAgent()
    await agent.register(bus)

    adapter = await Adapter.get_first(bus)

    # Create and register advertisement
    advert = Advertisement("Raspberry Pi Zero 2W", ["1234"], 0x0340, 60)
    await advert.register(bus, adapter)

    print("Advertising started...")
    await bus.wait_for_disconnect()


# Function to scan for BLE devices
def scan_devices():
    async def scan():
        print("Scanning for BLE devices...")
        async with BleakScanner() as scanner:
            while True:
                devices = await scanner.discover()
                for device in devices:
                    print(f"Found device: {device.name} - {device.address}")
                await asyncio.sleep(5)

    asyncio.run(scan())


# Start advertising and scanning using multiprocessing
if __name__ == "__main__":
    # Start advertising in a separate process
    advertiser = Process(target=lambda: asyncio.run(advertise()))
    advertiser.start()

    # Start scanning in a separate process
    scanner = Process(target=scan_devices)
    scanner.start()

    advertiser.join()
    scanner.join()
