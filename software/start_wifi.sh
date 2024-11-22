#!/bin/bash

# Script to reconnect to Wi-Fi

echo "Enabling wlan0 interface..."
sudo ifconfig wlan0 up

echo "Starting Wi-Fi services..."
sudo systemctl start wpa_supplicant
sudo systemctl start dhcpcd

echo "Attempting to reconnect to the Wi-Fi network..."
sudo dhclient wlan0

echo "Wi-Fi reconnected."
