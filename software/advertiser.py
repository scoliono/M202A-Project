import uuid  # For generating valid UUIDs
import asyncio
import json
import socket  # To get the hostname
import netifaces  # For getting MAC address
from bluez_peripheral.gatt.service import Service, ServiceCollection
from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CharFlags
from bluez_peripheral.advert import Advertisement
from bluez_peripheral.util import get_message_bus, Adapter
from sync import *
from typing import Dict, Optional


def get_wifi_mac_address():
    """Retrieve the MAC address of the Wi-Fi interface."""
    for iface in netifaces.interfaces():
        if iface.startswith("wlan"):  # Adjust based on your Wi-Fi interface name
            addr_info = netifaces.ifaddresses(iface)
            if netifaces.AF_LINK in addr_info:
                return addr_info[netifaces.AF_LINK][0]["addr"]
    return "00:00:00:00:00:00"  # Default if no Wi-Fi interface is found


# Define the BLE service
class FileSharingService(Service):
    def __init__(self, uuid):
        super().__init__(uuid, True)  # Custom service UUID
        self.client_requests = {}  # Map of client identifiers to requested files
        self.mac_address = get_wifi_mac_address()  # Retrieve Wi-Fi MAC address
        self.packages: Dict[str, Package] = {}

    # Read-only characteristic to advertise the list of packages
    @characteristic("BEF0", CharFlags.READ)
    def pkg_list(self, options):
        # Add the MAC address to the pkg list
        pkg_list_with_mac = {
            "mac": self.mac_address,  # Include the MAC address
            "pkgs": self.packages.keys(),
        }
        return bytes(json.dumps(pkg_list_with_mac), "utf-8")

    # Write-only characteristic to request chunk availability for a package
    @characteristic("BEF1", CharFlags.WRITE)
    def pkg_request(self, options):
        pass  # Placeholder (Python 3.9+ doesn't require this)

    # Setter for the package request characteristic
    @pkg_request.setter
    def pkg_request(self, value, options):
        # Use client-specific identifier from options
        client_id = options.device

        # Decode the package name from the client's write request
        requested_pkg = value.decode("utf-8")
        self.client_requests[client_id] = requested_pkg
        print(f"Client {client_id} requested file: {requested_pkg}")

    # Read-only characteristic to respond with package manifest
    @characteristic("BEF2", CharFlags.READ)
    def pkg_manifest(self, options):
        # Use client-specific identifier from options
        client_id = options.device

        # Check if this client has made a request
        if client_id in self.client_requests:
            requested_pkg = self.client_requests[client_id]
            if requested_pkg in self.packages:
                pkg = self.packages[requested_pkg]
                # Return manifest as a JSON list
                return bytes(json.dumps(pkg.get_manifest()), "utf-8")

        # Return an empty list if no valid request is found
        return bytes(json.dumps([]), "utf-8")


async def main():
    # Get the system D-Bus connection
    bus = await get_message_bus()

    # Retrieve the hostname for uniqueness
    hostname = socket.gethostname()

    # Generate a valid UUID for the service
    service_uuid = str(uuid.uuid4())  # Generate a proper 128-bit UUID

    # Mock data for files and chunks
    pkg = Package("SamplePackage", 1)
    pkg.write_chunk("/src/file1.txt", 0, b"Hello World", version=1)
    pkg.write_chunk("/src/file2.txt", 0, b"Some data", version=1)

    # Create and register the file-sharing service
    service = FileSharingService(service_uuid)
    service.packages[pkg.name] = pkg    # add our package
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
