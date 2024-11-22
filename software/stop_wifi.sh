#!/bin/bash

# Script to disconnect from Wi-Fi

echo "Stopping Wi-Fi services..."
sudo systemctl stop wpa_supplicant
sudo systemctl stop dhcpcd

echo "Disabling wlan0 interface..."
sudo ifconfig wlan0 down

echo "Wi-Fi disconnected. Ready for Wi-Fi Direct."
