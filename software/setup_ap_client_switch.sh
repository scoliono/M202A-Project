#!/bin/bash

# Script to set up Raspberry Pi for switching between AP mode and Client mode using NetworkManager and dnsmasq
# Usage: sudo ./setup_ap_client_switch.sh <AP_SSID> <AP_PASSWORD>

# Check for root privileges
if [ "$(id -u)" -ne 0 ]; then
    echo "Please run this script with sudo:"
    echo "sudo $0 <AP_SSID> <AP_PASSWORD>"
    exit 1
fi

# Check for input parameters
if [ "$#" -ne 2 ]; then
    echo "Usage: sudo $0 <AP_SSID> <AP_PASSWORD>"
    exit 1
fi

AP_SSID="$1"
AP_PASSWORD="$2"

# Validate password
if [ "${#AP_PASSWORD}" -lt 8 ] || [ "${#AP_PASSWORD}" -gt 63 ]; then
    echo "Error: The AP password must be between 8 and 63 characters."
    exit 1
fi

echo "Setting up Raspberry Pi with AP SSID: $AP_SSID"

# Ensure NetworkManager is installed
echo "Installing NetworkManager..."
apt-get update
apt-get install -y network-manager

# Enable NetworkManager and disable dhcpcd if necessary
echo "Enabling NetworkManager..."
systemctl enable NetworkManager
systemctl start NetworkManager
systemctl disable dhcpcd

# Install dnsmasq for DHCP server
echo "Installing dnsmasq..."
apt-get install -y dnsmasq

# Configure dnsmasq for wlan0
echo "Configuring dnsmasq..."
cat > /etc/dnsmasq.conf <<EOF
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
EOF

# Restart dnsmasq to apply changes
echo "Restarting dnsmasq..."
systemctl restart dnsmasq

# Create NetworkManager configuration for AP mode
echo "Creating NetworkManager configuration for AP mode..."
nmcli connection add type wifi ifname wlan0 con-name "AP_Mode" autoconnect no ssid "$AP_SSID"
nmcli connection modify "AP_Mode" 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$AP_PASSWORD"

# Create scripts for switching between modes
echo "Creating scripts for switching modes..."

# Script to switch to AP mode
cat > /usr/local/bin/ap_mode.sh <<'EOF'
#!/bin/bash
echo "Switching to Access Point mode..."
# Bring down client mode connection if active
nmcli connection down id "Client_Mode" 2>/dev/null
# Bring up AP mode connection
nmcli connection up id "AP_Mode"
# Assign a static IP address to wlan0
echo "Assigning static IP 192.168.4.1 to wlan0..."
sudo ifconfig wlan0 192.168.4.1 netmask 255.255.255.0
# Start dnsmasq for DHCP
echo "Starting DHCP server..."
sudo systemctl start dnsmasq
echo "Access Point mode enabled with IP 192.168.4.1."
EOF

# Make the script executable
chmod +x /usr/local/bin/ap_mode.sh

# Script to switch to Client mode
cat > /usr/local/bin/client_mode.sh <<'EOF'
#!/bin/bash
echo "Switching to Client mode..."
# Stop dnsmasq
echo "Stopping DHCP server..."
sudo systemctl stop dnsmasq
# Bring down AP mode connection if active
nmcli connection down id "AP_Mode" 2>/dev/null
# Bring up client mode connection
nmcli connection up id "Client_Mode"
echo "Client mode enabled."
EOF

chmod +x /usr/local/bin/client_mode.sh

# Save the current Wi-Fi network as "Client_Mode" if not already saved
echo "Ensuring current Wi-Fi network is saved as 'Client_Mode'..."
CURRENT_SSID=$(nmcli -t -f active,ssid dev wifi | grep "^yes" | cut -d: -f2)
if [ -n "$CURRENT_SSID" ]; then
    nmcli connection modify id "$CURRENT_SSID" connection.id "Client_Mode"
else
    echo "No active Wi-Fi connection detected. Please connect to a network first."
    exit 1
fi

echo "Setup complete!"
echo "You can switch to Access Point mode by running:"
echo "  sudo /usr/local/bin/ap_mode.sh"
echo "And switch back to Client mode by running:"
echo "  sudo /usr/local/bin/client_mode.sh"
