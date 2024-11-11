import asyncio
from bluez_peripheral.gatt.service import Service, ServiceCollection
from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CharFlags
from bluez_peripheral.gatt.descriptor import descriptor, DescriptorFlags as DescFlags
from bluez_peripheral.advert import Advertisement
from bluez_peripheral.util import get_message_bus, Adapter


# Define a custom BLE service
class CustomService(Service):
    def __init__(self):
        super().__init__("BEEF", True)  # Define the custom service UUID and set as primary
        self._data = b"Initial Data"

    # Define a read-only characteristic
    @characteristic("BEF0", CharFlags.READ)
    def readonly_characteristic(self, options):
        return bytes("Read-Only Value", "utf-8")

    # Define a write-only characteristic
    @characteristic("BEF1", CharFlags.WRITE)
    def writeonly_characteristic(self, options):
        pass  # Placeholder for write characteristic (not required in Python 3.9+)

    # Define the setter for the write-only characteristic
    @writeonly_characteristic.setter
    def writeonly_characteristic(self, value, options):
        self._data = value
        print(f"Characteristic updated with: {self._data.decode('utf-8')}")

    # Add a descriptor to the read-only characteristic
    @descriptor("BEF2", readonly_characteristic, DescFlags.READ)
    def readonly_descriptor(self, options):
        return bytes("Descriptor for Read-Only Characteristic", "utf-8")


async def main():
    # Get the system D-Bus connection
    bus = await get_message_bus()

    # Create and register the custom service
    service = CustomService()
    service_collection = ServiceCollection()
    service_collection.add_service(service)
    await service_collection.register(bus)

    # Advertise the custom service
    service_uuid = [service._uuid]  # Use _uuid since uuid is not directly accessible
    advert = Advertisement("Custom BLE Device", service_uuid, 0x0000, 60)  # Custom name and timeout
    adapter = await Adapter.get_first(bus)
    await advert.register(bus, adapter)

    print("Custom BLE Service is running and being advertised.")
    print("Use a BLE scanner app to connect and interact with the device.")

    # Keep the asyncio loop running
    await bus.wait_for_disconnect()


if __name__ == "__main__":
    asyncio.run(main())