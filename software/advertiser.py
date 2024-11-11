import uuid  # For generating valid UUIDs
import asyncio
import json
import socket  # To get the hostname
from bluez_peripheral.gatt.service import Service, ServiceCollection
from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CharFlags
from bluez_peripheral.advert import Advertisement
from bluez_peripheral.util import get_message_bus, Adapter


# Mock data for files and chunks
FILES = {
    "app1.apk": {"version": "1.0.0", "chunks": 4, "available_chunks": [0, 1, 2, 3]},
    "app2.apk": {"version": "2.3.1", "chunks": 8, "available_chunks": [0, 2, 4, 6]},
}


# Define the BLE service
class FileSharingService(Service):
    def __init__(self, uuid):
        super().__init__(uuid, True)  # Custom service UUID
        self.files = FILES  # File metadata
        self.client_requests = {}  # Map of client identifiers to requested files

    # Read-only characteristic to advertise the list of files
    @characteristic("BEF0", CharFlags.READ)
    def file_list(self, options):
        # Send the file list as a JSON string
        return bytes(json.dumps({k: {"version": v["version"], "chunks": v["chunks"]} for k, v in self.files.items()}), "utf-8")

    # Write-only characteristic to request chunk availability for a file
    @characteristic("BEF1", CharFlags.WRITE)
    def file_request(self, options):
        pass  # Placeholder (Python 3.9+ doesn't require this)

    # Setter for the file request characteristic
    @file_request.setter
    def file_request(self, value, options):
        # Use client-specific identifier from options
        client_id = options.device

        # Decode the file name from the client's write request
        requested_file = value.decode("utf-8")
        self.client_requests[client_id] = requested_file
        print(f"Client {client_id} requested file: {requested_file}")

    # Read-only characteristic to respond with available chunks
    @characteristic("BEF2", CharFlags.READ)
    def chunk_availability(self, options):
        # Use client-specific identifier from options
        client_id = options["device"]

        # Check if this client has made a request
        if client_id in self.client_requests:
            requested_file = self.client_requests[client_id]
            if requested_file in self.files:
                chunks = self.files[requested_file]["available_chunks"]
                # Return available chunks as a JSON list
                return bytes(json.dumps(chunks), "utf-8")

        # Return an empty list if no valid request is found
        return bytes(json.dumps([]), "utf-8")


async def main():
    # Get the system D-Bus connection
    bus = await get_message_bus()

    # Retrieve the hostname for uniqueness
    hostname = socket.gethostname()

    # Generate a valid UUID for the service
    service_uuid = str(uuid.uuid4())  # Generate a proper 128-bit UUID

    # Create and register the file-sharing service
    service = FileSharingService(service_uuid)
    service_collection = ServiceCollection()
    service_collection.add_service(service)
    await service_collection.register(bus)

    # Advertise the file-sharing service using the hostname
    advert = Advertisement(f"FileShare-{hostname}", [service._uuid], 0x0000, 0)
    adapter = await Adapter.get_first(bus)
    await advert.register(bus, adapter)

    print(f"File Sharing Service is running as '{hostname}' and being advertised.")
    print("Use a BLE scanner app to connect and interact with the service.")

    # Keep the asyncio loop running
    await bus.wait_for_disconnect()


if __name__ == "__main__":
    asyncio.run(main())
