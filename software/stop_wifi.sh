#!/bin/bash

echo "Disabling wlan0 interface..."
sudo ifconfig wlan0 down  # Directly bring up the interface