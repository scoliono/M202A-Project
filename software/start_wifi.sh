#!/bin/bash

# Script to reconnect to Wi-Fi

echo "Enabling wlan0 interface..."
sudo ip link set wlan0 up

echo "Starting wpa_supplicant service..."
sudo systemctl start wpa_supplicant

echo "Requesting IP address for wlan0..."
sudo dhclient wlan0

echo "Wi-Fi reconnected."
