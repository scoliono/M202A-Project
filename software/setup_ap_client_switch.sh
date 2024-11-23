#!/bin/bash

# Script to set up Raspberry Pi for switching between AP mode and Client mode
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

# Validate SSID and password
if [ "${#AP_PASSWORD}" -lt 8 ] || [ "${#AP_PASSWORD}" -gt 63 ]; then
    echo "Error: The AP password must be between 8 and 63 characters."
    exit 1
fi

echo "Setting up Raspberry Pi with AP SSID: $AP_SSID"

echo "Updating system packages..."
apt-get update
apt-get upgrade -y

echo "Installing required packages..."
apt-get install -y hostapd dnsmasq

echo "Stopping services if running..."
systemctl stop hostapd
systemctl stop dnsmasq

echo "Configuring dhcpcd.conf for AP and Client modes..."

# Backup the original dhcpcd.conf
cp /etc/dhcpcd.conf /etc/dhcpcd.conf.orig

# Create dhcpcd.conf for AP mode
cat > /etc/dhcpcd.conf.ap <<EOF
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
EOF

# Create dhcpcd.conf for Client mode (original configuration)
cp /etc/dhcpcd.conf.orig /etc/dhcpcd.conf.client

echo "Configuring hostapd..."

# Create hostapd configuration file
cat > /etc/hostapd/hostapd.conf <<EOF
interface=wlan0
driver=nl80211
ssid=$AP_SSID
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$AP_PASSWORD
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF

# Set DAEMON_CONF path
sed -i 's|#DAEMON_CONF=""/DAEMON_CONF=""/DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd

echo "Configuring dnsmasq..."

# Backup the original dnsmasq.conf
mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig

# Create dnsmasq configuration file
cat > /etc/dnsmasq.conf <<EOF
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
EOF

echo "Configuring wpa_supplicant for Client mode..."

# Ensure wpa_supplicant.conf exists
if [ ! -f /etc/wpa_supplicant/wpa_supplicant.conf ]; then
    touch /etc/wpa_supplicant/wpa_supplicant.conf
    chmod 600 /etc/wpa_supplicant/wpa_supplicant.conf
fi

# Make sure country code and control interface are set
sed -i '/^country=/d' /etc/wpa_supplicant/wpa_supplicant.conf
sed -i '/^ctrl_interface=/d' /etc/wpa_supplicant/wpa_supplicant.conf
sed -i '/^update_config=/d' /etc/wpa_supplicant/wpa_supplicant.conf

cat <<EOF >> /etc/wpa_supplicant/wpa_supplicant.conf
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
EOF

echo "Creating scripts to switch between AP and Client modes..."

# Script to switch to AP mode
cat > /usr/local/bin/ap_mode.sh <<'EOF'
#!/bin/bash

echo "Switching to Access Point mode..."

# Stop client services
systemctl stop wpa_supplicant.service

# Copy AP dhcpcd configuration
cp /etc/dhcpcd.conf.ap /etc/dhcpcd.conf

# Restart dhcpcd service
systemctl restart dhcpcd.service

# Start AP services
systemctl start dnsmasq.service
systemctl start hostapd.service

echo "Access Point mode enabled."
EOF

chmod +x /usr/local/bin/ap_mode.sh

# Script to switch to Client mode
cat > /usr/local/bin/client_mode.sh <<'EOF'
#!/bin/bash

echo "Switching to Client mode..."

# Stop AP services
systemctl stop hostapd.service
systemctl stop dnsmasq.service

# Copy client dhcpcd configuration
cp /etc/dhcpcd.conf.client /etc/dhcpcd.conf

# Restart dhcpcd service
systemctl restart dhcpcd.service

# Start client services
systemctl start wpa_supplicant.service

echo "Client mode enabled."
EOF

chmod +x /usr/local/bin/client_mode.sh

echo "Disabling services from starting at boot..."

# Disable AP services at boot
systemctl disable hostapd.service
systemctl disable dnsmasq.service

# Enable wpa_supplicant at boot
systemctl enable wpa_supplicant.service

echo "Setup complete!"

echo "You can switch to Access Point mode by running:"
echo "sudo /usr/local/bin/ap_mode.sh"

echo "And switch back to Client mode by running:"
echo "sudo /usr/local/bin/client_mode.sh"
