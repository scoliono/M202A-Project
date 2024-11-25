#!/bin/bash

# setup_ap.sh: Configure Raspberry Pi as a Wi-Fi Access Point
# Usage: sudo ./setup_ap.sh <device_name> [wifi_password]

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run with sudo or as root."
   exit 1
fi

# Check if device name is provided
if [ -z "$1" ]; then
    echo "Usage: sudo $0 <device_name> [wifi_password]"
    exit 1
fi

DEVICE_NAME="$1"

# Check if Wi-Fi password is provided, else prompt for one
if [ -z "$2" ]; then
    read -s -p "Enter a strong Wi-Fi password for the AP: " WIFI_PASSWORD
    echo
    read -s -p "Confirm the password: " WIFI_PASSWORD_CONFIRM
    echo
    if [ "$WIFI_PASSWORD" != "$WIFI_PASSWORD_CONFIRM" ]; then
        echo "Passwords do not match. Exiting."
        exit 1
    fi
else
    WIFI_PASSWORD="$2"
fi

# Validate Wi-Fi password length (minimum 8 characters)
if [ ${#WIFI_PASSWORD} -lt 8 ]; then
    echo "The Wi-Fi password must be at least 8 characters long."
    exit 1
fi

echo "Configuring Raspberry Pi as an Access Point with SSID '${DEVICE_NAME}_AP'..."

# Update and upgrade
apt-get update
apt-get upgrade -y

# Install necessary packages
apt-get install hostapd dnsmasq -y

# Stop services if they are running
systemctl stop hostapd
systemctl stop dnsmasq

# Enable hostapd
systemctl unmask hostapd
systemctl enable hostapd

# Configure static IP for wlan0
# Backup dhcpcd.conf if not already backed up
if [ ! -f /etc/dhcpcd.conf.bak ]; then
    cp /etc/dhcpcd.conf /etc/dhcpcd.conf.bak
fi

# Remove existing wlan0 configurations
sed -i '/^interface wlan0$/d' /etc/dhcpcd.conf
sed -i '/^static ip_address=192.168.4.1\/24$/d' /etc/dhcpcd.conf
sed -i '/^nohook wpa_supplicant$/d' /etc/dhcpcd.conf

cat >> /etc/dhcpcd.conf <<EOF

interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
EOF

# Restart dhcpcd
service dhcpcd restart

# Configure dnsmasq
# Backup dnsmasq.conf if not already backed up
if [ ! -f /etc/dnsmasq.conf.orig ]; then
    mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
fi

cat > /etc/dnsmasq.conf <<EOF
interface=wlan0      # Use the wireless interface
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
EOF

# Configure hostapd
cat > /etc/hostapd/hostapd.conf <<EOF
interface=wlan0
driver=nl80211
ssid=${DEVICE_NAME}_AP
hw_mode=g
channel=7
wmm_enabled=1
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=${WIFI_PASSWORD}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

# Specify the configuration file for hostapd
sed -i '/^#DAEMON_CONF=.*/d' /etc/default/hostapd
echo 'DAEMON_CONF="/etc/hostapd/hostapd.conf"' >> /etc/default/hostapd

# Enable IP forwarding
sed -i '/^#net.ipv4.ip_forward=1/s/^#//g' /etc/sysctl.conf
sysctl -p

# Configure NAT between wlan0 and eth0
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# Save iptables rule
sh -c "iptables-save > /etc/iptables.ipv4.nat"

# Ensure the iptables rule is applied on boot
if ! grep -Fxq "iptables-restore < /etc/iptables.ipv4.nat" /etc/rc.local; then
    sed -i '/^exit 0/i iptables-restore < /etc/iptables.ipv4.nat' /etc/rc.local
fi

# Start services
systemctl restart hostapd
systemctl restart dnsmasq

echo "Access Point setup is complete."
echo "SSID: ${DEVICE_NAME}_AP"
echo "Password: ${WIFI_PASSWORD}"
