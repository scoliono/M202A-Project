#!/bin/bash

# Script to disconnect from Wi-Fi

echo "Stopping wpa_supplicant service..."
sudo systemctl stop wpa_supplicant

echo "Disabling wlan0 interface..."
sudo ip link set wlan0 down

echo "Flushing IP address for wlan0..."
sudo ip addr flush dev wlan0

echo "Wi-Fi disconnected. Ready for Wi-Fi Direct."
