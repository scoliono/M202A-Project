#!/bin/bash

echo "Stopping wpa_supplicant service..."
sudo systemctl stop wpa_supplicant
sudo systemctl disable wpa_supplicant

echo "Disabling wlan0 interface..."
sudo ifconfig wlan0 down  # Use ifconfig as it works reliably on your setup
sudo ip addr flush dev wlan0

echo "Wi-Fi fully disabled. Ready for Wi-Fi Direct."
