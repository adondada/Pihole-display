#!/usr/bin/python3
import sys
import os
import time
import sqlite3
import datetime
import subprocess
import psutil
from PIL import Image, ImageDraw, ImageFont

# Add the local library folder to path
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'waveshare_epd'))
from waveshare_epd import epd2in13_V4

# ==========================================
#  USER SETTINGS
# ==========================================
REFRESH_SECONDS = 60
DB_FILE = "/etc/pihole/pihole-FTL.db"

# Display Names
USER_NAME = "adondada"  # Change this to your name
HEADER_TAG = "Pi-hole"  # Small text in the header
# ==========================================

def get_ip():
    try:
        cmd = "hostname -I | cut -d' ' -f1"
        IP = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
        return IP
    except:
        return "No IP"

def get_pihole_data():
    try:
        now = datetime.datetime.now()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        ts_midnight = int(midnight.timestamp())
        ts_24h = int(time.time()) - 86400

        # Connect to Database (Read Only)
        # We use uri=True to allow opening in read-only mode to prevent locking
        conn = sqlite3.connect(f"file:{DB_FILE}?mode=ro", uri=True)
        c = conn.cursor()

        # Midnight Stats (Since 00:00 today)
        c.execute("SELECT count(id) FROM queries WHERE timestamp >= ?", (ts_midnight,))
        queries_today = c.fetchone()[0]

        # Blocked Today (Status NOT IN 2=Forwarded, 3=Cached, etc.)
        c.execute("SELECT count(id) FROM queries WHERE timestamp >= ? AND status NOT IN (2, 3, 12, 13, 14)", (ts_midnight,))
        blocked_today = c.fetchone()[0]

        # 24H Total (Rolling Window to match dashboard)
        c.execute("SELECT count(id) FROM queries WHERE timestamp >= ?", (ts_24h,))
        total_24h = c.fetchone()[0]

        conn.close()

        ratio = 0.0
        if queries_today > 0:
            ratio = round((blocked_today / queries_today) * 100, 1)

        return {
            'ads_blocked': blocked_today,
            'ratio': ratio,
            'total_24h': total_24h
        }

    except Exception as e:
        print(f"DB Error: {e}")
        return None

def get_system_stats():
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()
    ram_used = round(ram.used / 1024 / 1024)
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = round(int(f.read()) / 1000, 1)
    except:
        temp = "??"
    return cpu, ram_used, temp

def main():
    # Fonts - Standard Linux paths
    font_main = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 16)
    font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)
    font_tiny = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 10) 
    font_big = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)

    print(f"Starting Display Script for {USER_NAME}...")

    while True:
        try:
            epd = epd2in13_V4.EPD()
            epd.init()

            ip_addr = get_ip()
            pi_data = get_pihole_data()
            cpu, ram_u, temp = get_system_stats()

            # Create Image (White Background 255)
            image = Image.new('1', (epd.height, epd.width), 255) 
            draw = ImageDraw.Draw(image)

            # --- HEADER (Black Bar) ---
            draw.rectangle([(0,0), (250, 20)], fill=0) 
            draw.text((5, 2), f"IP: {ip_addr}", font=font_main, fill=255)
            # Tag on the right side
            draw.text((200, 5), HEADER_TAG, font=font_tiny, fill=255)
            
            # --- SYSTEM STATS (Right Side) ---
            draw.text((150, 25), f"CPU: {cpu}%", font=font_small, fill=0)
            draw.text((150, 45), f"RAM: {ram_u}M", font=font_small, fill=0)
            draw.text((150, 65), f"{temp}°C", font=font_small, fill=0)

            # --- PI-HOLE STATS (Left Side) ---
            if pi_data:
                # Main Blocked Count (Since Midnight)
                draw.text((5, 25), "Blocked (Today):", font=font_small, fill=0)
                draw.text((5, 40), str(pi_data['ads_blocked']), font=font_big, fill=0)
                
                # Ratio
                draw.text((5, 75), f"Ratio: {pi_data['ratio']}%", font=font_main, fill=0)
                
                # Total 24h (Small reference at bottom)
                draw.text((5, 92), f"Total 24h: {pi_data['total_24h']}", font=font_tiny, fill=0)
            else:
                draw.text((5, 40), "Loading...", font=font_main, fill=0)

            # --- FOOTER ---
            curr_time = time.strftime("%H:%M")
            draw.line([(0, 105), (250, 105)], fill=0, width=1)
            
            # Time on Left
            draw.text((5, 107), f"Updated: {curr_time}", font=font_small, fill=0)
            
            # User Name on Right
            draw.text((175, 107), USER_NAME, font=font_small, fill=0)

            # Rotate 180 (for upside down mounting)
            image = image.rotate(180) 
            
            # Update and Sleep
            epd.display(epd.getbuffer(image))
            epd.sleep()
            
            time.sleep(REFRESH_SECONDS)

        except IOError as e:
            print(f"IOError: {e}")
            time.sleep(10)
        except KeyboardInterrupt:
            epd = epd2in13_V4.EPD()
            epd.init()
            epd.Clear(0xFF)
            epd.sleep()
            print("Exiting...")
            break

if __name__ == '__main__':
    main()
