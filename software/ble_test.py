import asyncio
from dbus_next.aio import MessageBus
from dbus_next.service import ServiceInterface, method
from bleak import BleakScanner, BleakClient

import config


# BLE Advertising Code
class BLEAdvertisement(ServiceInterface):
    def __init__(self, bus):
        super().__init__('org.bluez.LEAdvertisement1')
        self.bus = bus

    @method()
    def Release(self):
        print("Advertisement released")

async def advertise():
    bus = await MessageBus().connect()
    adapter = 'hci0'
    advertisement_path = '/org/bluez/example/advertisement'
    advertisement = BLEAdvertisement(bus)
    await bus.export(advertisement_path, advertisement)

    bluez = bus.get_proxy_object('org.bluez', '/', None)
    adapter_interface = bluez.get_interface('org.bluez.LEAdvertisingManager1', f'/org/bluez/{adapter}')
    advertisement_params = {
        'Type': 'peripheral',
        'ServiceUUIDs': ['12345678-1234-5678-1234-56789abcdef0'],
        'LocalName': config.LOCAL_DEVICE_NAME,
    }

    await adapter_interface.call_register_advertisement(advertisement_path, advertisement_params)
    print("Advertisement registered")

    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        await adapter_interface.call_unregister_advertisement(advertisement_path)
        print("Advertisement unregistered")

# BLE Scanning and Connecting Code
TARGET_DEVICE_NAME = config.TARGET_DEVICE_NAME

async def scan_and_connect():
    while True:
        print("Scanning for BLE devices...")
        devices = await BleakScanner.discover()
        for device in devices:
            print(f"Found device: {device.name} ({device.address})")
            if device.name == TARGET_DEVICE_NAME:
                print(f"Connecting to {TARGET_DEVICE_NAME} ({device.address})")
                async with BleakClient(device.address) as client:
                    print(f"Connected to {TARGET_DEVICE_NAME}")
                    services = await client.get_services()
                    print(f"Services: {services}")
                return
        await asyncio.sleep(5)

# Main function to run both tasks
async def main():
    await asyncio.gather(advertise(), scan_and_connect())

asyncio.run(main())
