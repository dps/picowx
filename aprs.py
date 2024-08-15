import WIFI_CONFIG
from network_manager import NetworkManager
import time
import uasyncio
import ujson
import math
from urllib import urequest
from picographics import PicoGraphics, DISPLAY_INKY_PACK

graphics = PicoGraphics(DISPLAY_INKY_PACK)

WIDTH, HEIGHT = graphics.get_bounds()

def draw_arrow(center_x, center_y, length, heading):
    RAD_45_DEGREES = 0.7853981633974483   
    # Convert heading to radians
    heading_rad = math.radians(90 - heading)
    
    # Calculate the start point of the arrow shaft
    start_x = center_x - int(math.cos(heading_rad) * (length / 2))
    start_y = center_y + int(math.sin(heading_rad) * (length / 2))
    
    # Calculate the end point of the arrow shaft
    end_x = center_x + int(math.cos(heading_rad) * (length / 2))
    end_y = center_y - int(math.sin(heading_rad) * (length / 2))
    
    # Draw the arrow shaft
    graphics.line(start_x, start_y, end_x, end_y, 2)

    arrowhead_length = length / 4  # Length of each side of the arrowhead
    
    ah_x = center_x + int(math.cos(heading_rad+RAD_45_DEGREES) * (arrowhead_length))
    ah_y = center_y - int(math.sin(heading_rad+RAD_45_DEGREES) * (arrowhead_length))

    graphics.line(ah_x, ah_y, end_x, end_y, 2)

    ah_x = center_x + int(math.cos(heading_rad-RAD_45_DEGREES) * (arrowhead_length))
    ah_y = center_y - int(math.sin(heading_rad-RAD_45_DEGREES) * (arrowhead_length))

    graphics.line(ah_x, ah_y, end_x, end_y, 2)

def time_in_tz(unix_timestamp, tz_offset):
    if tz_offset == None:
        tz_offset = 0
    # Specify your timezone offset in seconds
    # For example, if your timezone is UTC+2 (Central European Summer Time)
    # offset would be 2 hours * 3600 seconds/hour = 7200 seconds
    timezone_offset = tz_offset * 3600  # Adjust this offset according to your timezone

    # Convert to local time by applying the timezone offset
    local_timestamp = unix_timestamp + timezone_offset
    local_time = time.localtime(local_timestamp)

    # Format the local time into a readable string
    formatted_time = "{:02d}-{:02d} {:02d}:{:02d}".format(
        local_time[1], local_time[2],
        local_time[3], local_time[4]
    )
    if tz_offset == 0:
        formatted_time += "UTC"

    return formatted_time

display_ssid = None

def status_handler(mode, status, ip):
    global display_ssid
    graphics.set_font("bitmap8")
    graphics.set_update_speed(2)
    graphics.set_pen(15)
    graphics.clear()
    graphics.set_pen(0)
    graphics.text("Network: {}".format(display_ssid), 10, 10, scale=2)
    status_text = "Connecting..."
    if status is not None:
        if status:
            status_text = "Connection successful!"
        else:
            status_text = "Connection failed!"

    graphics.text(status_text, 10, 30, scale=2)
    graphics.text("IP: {}".format(ip), 10, 60, scale=2)
    graphics.update()

network_manager = NetworkManager(WIFI_CONFIG.COUNTRY, status_handler=status_handler)

def aprs_update(ssid, psk, callsign, api_key, nickname=None, tz_offset=None):
    global display_ssid
    display_ssid = ssid
    uasyncio.get_event_loop().run_until_complete(network_manager.client(ssid, psk))

    if not nickname:
        nickname = callsign
    
    url = f"https://api.aprs.fi/api/get?name={callsign}&what=wx&apikey={api_key}&format=json"
    j = ujson.load(urequest.urlopen(url))

    graphics.set_update_speed(1)
    graphics.set_pen(15)
    graphics.clear()
    graphics.set_pen(0)
    graphics.set_font("bitmap6")
    graphics.text(nickname, 10, 10, wordwrap=WIDTH - 20, scale=4)
    graphics.set_font("bitmap8")
    temp = j["entries"][0]["temp"]
    humidity = j["entries"][0]["humidity"]
    pressure = j["entries"][0]["pressure"]
    wind_speed = j["entries"][0]["wind_speed"]
    wind_direction = j["entries"][0]["wind_direction"]
    draw_arrow(140, 94, 30, int(wind_direction))

    graphics.text(f"{temp}C {humidity}% {pressure}mbar", 10, 50, wordwrap=WIDTH - 20, scale=3)
    graphics.text(f"{wind_speed} m/s", 10, 80, wordwrap=WIDTH - 20, scale=3)
    local_time = time_in_tz(int(j["entries"][0]["time"]), tz_offset)
    graphics.set_font("bitmap6")
    graphics.text(f"Updated {local_time}", 10, 110, wordwrap=WIDTH - 20, scale=2)

    graphics.update()
