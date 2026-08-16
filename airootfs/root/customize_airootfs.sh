#!/bin/bash
echo ">>> Welcome to Alcor GNU/Linux Installer <<<"
echo "We are making settings for you"
echo "alcorlinux.org"

mkdir -p /etc/sddm.conf.d
cat > /etc/sddm.conf.d/autologin.conf << 'EOF'
[Autologin]
User=alcor
Session=xfce.desktop
Relogin=false
EOF