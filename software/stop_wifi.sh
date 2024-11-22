#!/bin/bash

echo "Stopping and disabling Wi-Fi services..."

# Disable wpa_supplicant to prevent auto-restart
sudo systemctl stop wpa_supplicant
sudo systemctl disable wpa_supplicant

# Disable dhcpcd (if installed)
sudo systemctl stop dhcpcd 2>/dev/null || echo "dhcpcd not installed"
sudo systemctl disable dhcpcd 2>/dev/null || echo "dhcpcd service not available"

# Bring the wlan0 interface down and flush IP
echo "Disabling wlan0 interface..."
sudo ip link set wlan0 down
sudo ip addr flush dev wlan0

echo "Wi-Fi fully disabled. Ready for Wi-Fi Direct."
