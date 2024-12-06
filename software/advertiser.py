import asyncio
import json
import random
import socket  # To get the hostname
import netifaces  # For getting MAC address
from bluez_peripheral.gatt.service import Service, ServiceCollection
from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CharFlags
from bluez_peripheral.advert import Advertisement
from bluez_peripheral.agent import NoIoAgent
from bluez_peripheral.util import get_message_bus, Adapter
from typing import Callable, Dict, Optional

from config import *
from sync import *


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
    def __init__(self, hostname: str, packages: Optional[Dict[str, Package]] = {}, on_manifest: Optional[Callable] = None):
        super().__init__(UUID, True)  # Custom service UUID
        self.hostname = hostname
        self.client_requests = {}  # Map of client identifiers to requested files
        self.mac_address = get_wifi_mac_address()  # Retrieve Wi-Fi MAC address
        self.packages: Dict[str, Package] = packages
        self.on_manifest = on_manifest

    # Read-only characteristic to advertise the list of packages
    @characteristic(PKG_LIST_R, CharFlags.READ)
    def pkg_list(self, options):
        # Add the MAC address to the pkg list
        pkg_list_with_mac = {
            "ssid": hostname,
            "mac": self.mac_address,  # Include the MAC address
            "pkgs": list(self.packages.keys())
        }
        return bytes(json.dumps(pkg_list_with_mac), "utf-8")

    # Write-only characteristic to request chunk availability for a package
    @characteristic(PKG_REQUEST_W, CharFlags.WRITE)
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
    @characteristic(PKG_MANIFEST_R, CharFlags.READ)
    def read_pkg_manifest(self, options):
        # Use client-specific identifier from options
        client_id = options.device

        # Check if this client has made a request
        if client_id in self.client_requests:
            requested_pkg = self.client_requests[client_id]
            if requested_pkg in self.packages:
                pkg = self.packages[requested_pkg]
                # Return manifest as a JSON list
                return bytes(pkg.load_manifest(), "utf-8")

        # Return an empty list if no valid request is found
        return bytes(json.dumps([]), "utf-8")

    # Write-only characteristic to supply package manifest
    @characteristic(PKG_MANIFEST_W, CharFlags.WRITE)
    def pkg_manifest(self, options):
        pass  # Placeholder (Python 3.9+ doesn't require this)

    # Setter for the package manifest characteristic
    @pkg_manifest.setter
    def write_pkg_manifest(self, value, options):
        try:
            decoded = value.decode("utf-8")
            parsed = json.loads(decoded)
            self.on_manifest(parsed)
        except Exception as e:
            print(f'Failed to process manifest: {str(e)}')


async def ble_server(packages = None, on_manifest = None):
    """
    Hosts the FileSharingService over Bluetooth LE.
    """
    # Get the system D-Bus connection
    bus = await get_message_bus()

    # Retrieve the hostname for uniqueness
    hostname = socket.gethostname()

    # Create and register the file-sharing service
    service = FileSharingService(hostname, packages, on_manifest=on_manifest)
    service_collection = ServiceCollection()
    service_collection.add_service(service)
    await service_collection.register(bus)

    # how long to spend advertising before scanning
    timeout = random.randint(15, 25)

    # Advertise the file-sharing service using the hostname
    advert = Advertisement(f"FileShare-{hostname}", [service._uuid], 0x0040, timeout)
    adapter = await Adapter.get_first(bus)
    await advert.register(bus, adapter)

    agent = NoIoAgent()
    await agent.register(bus)

    print(f"File Sharing Service is running as '{hostname}' and being advertised.")
    print("Use a BLE scanner app to connect and interact with the service.")

    await asyncio.sleep(timeout)
    await agent.unregister(bus)


if __name__ == "__main__":
    asyncio.run(server())
