# Pi-hole Status Display (Waveshare 2.13" V4 e-Paper)

A lightweight Python script to display Pi-hole statistics and system information on a Raspberry Pi Zero 2 W using the **Waveshare 2.13inch V4 e-Paper HAT**.

The display is designed to be **Auth-Free** (no API keys required) by reading the Pi-hole FTL database directly locally. It is optimized for longevity with inverted layouts and efficient refreshing.

## Features
* **Zero API Keys:** Reads directly from `/etc/pihole/pihole-FTL.db`.
* **Crisp Layout:** White background, Black text.
* **Dual Stats:** * "Blocked Today": Counts from Midnight (00:00).
  * "Total 24h": Rolling 24-hour window (Matches Pi-hole Dashboard).
* **System Info:** IP Address, CPU Load, RAM Usage, Temperature.
* **Customizable:** Header tag and Footer signature.
* **Rotated 180°:** Optimized for top-mounted GPIO headers.

## Hardware
* Raspberry Pi Zero 2 W (or any Pi model).
* Waveshare 2.13inch e-Paper HAT (Version 4).

## Installation

### 1. Enable SPI
Enable the SPI interface on your Raspberry Pi:
```
sudo raspi-config
# Interface Options -> SPI -> Yes
sudo reboot
```

### 2. Install Dependencies
Install the required system and Python libraries:
```
sudo apt-get update
sudo apt-get install python3-pip python3-pil python3-numpy python3-psutil git -y
sudo pip3 install RPi.GPIO spidev
```

### 3. Install Waveshare Drivers
Clone the official Waveshare repo and copy the specific V4 library to your project folder:
```
mkdir ~/pihole-display
cd ~/pihole-display


# Clone Waveshare drivers
git clone [https://github.com/waveshare/e-Paper](https://github.com/waveshare/e-Paper)
# Copy the V4 driver to your local folder
cp -r e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd .
# Clean up
rm -rf e-Paper
```

### 4. Install the Script
Copy main.py into the folder.
```
nano main.py
# Paste the content of main.py here
```
Edit the USER_NAME variable at the top of the script to your liking.


### Automatic Start (Systemd Service)
To make the screen start automatically on boot, create a system service.

### 1. Create the service file:
```
 sudo nano /etc/systemd/system/pihole-display.service
```

### 2. Paste the following configuration: 
(User=root is set so it has permission to read the database, but for me it works without it too)

```
[Unit]
Description=Pi-hole e-Paper Display
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/home/pi/pihole-display
ExecStart=/usr/bin/python3 /home/pi/pihole-display/main.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

### 3. Enable it and start

```sudo systemctl daemon-reload
sudo systemctl enable pihole-display.service
sudo systemctl start pihole-display.service
```


### Troubleshooting
"DB Read Error": Ensure the service is running as root (Admin), as the Pi-hole database is locked to standard users.

"IOError": Check your HAT connection. Ensure SPI is enabled in raspi-config.
