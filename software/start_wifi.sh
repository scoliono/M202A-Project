#!/bin/bash

echo "Re-enabling Wi-Fi services..."

# Re-enable and start wpa_supplicant
sudo systemctl enable wpa_supplicant
sudo systemctl start wpa_supplicant

# Re-enable dhcpcd (if installed)
sudo systemctl enable dhcpcd 2>/dev/null || echo "dhcpcd not installed"
sudo systemctl start dhcpcd 2>/dev/null || echo "dhcpcd service not available"

# Bring the wlan0 interface up and request a new IP
echo "Enabling wlan0 interface..."
sudo ip link set wlan0 up
sudo dhclient wlan0

echo "Wi-Fi reconnected."
