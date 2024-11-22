#!/bin/bash

echo "Re-enabling Wi-Fi services..."

# Re-enable and start wpa_supplicant
sudo systemctl enable wpa_supplicant
sudo systemctl start wpa_supplicant

# Bring wlan0 interface up and request an IP address
sudo ifconfig wlan0 up
sudo dhclient wlan0

echo "Wi-Fi reconnected."
