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
    RAD_45_DEGREES = 0.7853981633974483 * 2   
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

    arrowhead_width = length / 2  # Length of each side of the arrowhead
    
    ah_x = center_x + int(math.cos(heading_rad+RAD_45_DEGREES) * (arrowhead_width))
    ah_y = center_y - int(math.sin(heading_rad+RAD_45_DEGREES) * (arrowhead_width))

    graphics.line(ah_x, ah_y, end_x, end_y, 2)

    ah_x = center_x + int(math.cos(heading_rad-RAD_45_DEGREES) * (arrowhead_width))
    ah_y = center_y - int(math.sin(heading_rad-RAD_45_DEGREES) * (arrowhead_width))

    graphics.line(ah_x, ah_y, end_x, end_y, 2)

def draw_tides(center_x, center_y, tide_data, width=100, height=24, rotation=0):
    if not tide_data or "predictions" not in tide_data:
        return
        
    predictions = tide_data["predictions"]
    if len(predictions) < 2:
        return
        
    # Find min and max values for scaling
    values = [float(p["v"]) for p in predictions]
    min_tide = min(values) - 2
    max_tide = max(values)
    tide_range = max_tide - min_tide
    
    # Plot points and connect them
    prev_x = prev_y = None
    for i, pred in enumerate(predictions):
        if rotation == 90:
            # For 90 degree rotation, swap width/height and flip coordinates
            progress = i / (len(predictions) - 1)
            value = float(pred["v"])
            x = int(center_x + int(((value - min_tide) / tide_range) * width) - width//2)
            # Flip y-coordinate by subtracting from height
            y = int(center_y + height//2 - int(progress * height))
        else:
            # Original horizontal layout
            x = int(center_x - width//2 + (i * width) // (len(predictions) - 1))
            value = float(pred["v"])
            y = int(center_y - int(((value - min_tide) / tide_range) * height))
            
        # Check if time ends in :00 (on the hour)
        if pred["t"].split()[1].endswith(":00"):
            if rotation == 90:
                # Draw horizontal line for rotated view
                graphics.line(x, y, int(center_x - width//2), y, 3)
            else:
                # Draw vertical line for normal view
                graphics.line(x, y, x, int(center_y + height//2), 3)
            
        prev_x, prev_y = x, y

def time_in_tz(unix_timestamp, tz_offset, timeFormat="24"):
    if tz_offset == None:
        tz_offset = 0
    local_time = time.localtime(unix_timestamp + (tz_offset * 3600))
    
    hour = local_time[3]
    if timeFormat == "12":
        am_pm = "a" if hour < 12 else "p"
        hour = 12 if hour == 0 else hour % 12 or 12
        formatted_time = f"{local_time[1]:02d}-{local_time[2]:02d} {hour}:{local_time[4]:02d}{am_pm}"
    else:
        formatted_time = f"{local_time[1]:02d}-{local_time[2]:02d} {hour:02d}:{local_time[4]:02d}"
    
    return formatted_time + ("UTC" if tz_offset == 0 else "")

display_ssid = None
current_ssid = None  # Track the currently connected network

def status_handler(mode, status, ip):
    global display_ssid, current_ssid
    if status:  # If connection successful
        current_ssid = display_ssid  # Update current network
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

def celsius_to_fahrenheit(celsius):
    return (celsius * 9/5) + 32

def drawLabel(label, x, y, scale=1):
    graphics.set_font("bitmap6")
    graphics.text(label, x, y, scale=scale, angle=90)
    return x - (9 * scale) - 4 # Return next x position for portrait mode

def drawValue(value, x, y, scale=3):
    graphics.set_font("bitmap8")
    graphics.text(str(value), x, y, scale=scale, angle=90)
    return x - (8 * scale) - 4 # Return next x position based on scale

def aprs_update(config, nickname=None, tz_offset=None):
    ssid = config['ssid']
    
    psk = config['password']
    callsign = config['callsign']
    api_key = config['api']
    units = config.get('units', "C").upper()
    timeFormat = config.get('time', "24")

    tide_station = config.get('tide_station')  # Get tide station if available
    
    global display_ssid, current_ssid
    display_ssid = ssid
    
    # Only reconnect if we're not already connected to the desired network
    if current_ssid != ssid:
        uasyncio.get_event_loop().run_until_complete(network_manager.client(ssid, psk))

    if not nickname:
        nickname = callsign
    
    # Get APRS data
    url = f"https://api.aprs.fi/api/get?name={callsign}&what=wx&apikey={api_key}&format=json"
    print("Getting APRS data: ", url)
    aprs_data = ujson.load(urequest.urlopen(url))

    # Get tide data if station is configured
    tide_info = ""
    tide_data = None
    tide_time = None
    tide_type = None

    if tide_station:
        try:
            # Get current time and time 24 hours from now
            current = time.time()  # 1 hour ago
            end_time = current + (24 * 3600)  # 24 hours after current
            
            # Format dates and times as YYYYMMDD HH:MM
            current_dt = time.localtime(current)
            
            begin_date = f"{current_dt[0]}{current_dt[1]:02d}{current_dt[2]:02d}%20{current_dt[3]:02d}:{current_dt[4]:02d}"

            # Get predictions for next 24 hours
            tide_url = f"https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date={begin_date}&range=24&station={tide_station}&product=predictions&datum=MLLW&time_zone=gmt&units=english&format=json&interval=15"
            print("Getting tide data: ", tide_url)
            tide_data = ujson.load(urequest.urlopen(tide_url))
            if "predictions" in tide_data and len(tide_data["predictions"]) > 0:
                current_tide = float(tide_data["predictions"][0]["v"])
                # Find next extreme (high or low tide)
                next_extreme = None
                prev_value = float(tide_data["predictions"][0]["v"])
                for pred in tide_data["predictions"][1:]:
                    curr_value = float(pred["v"])
                    if (prev_value < curr_value and curr_value > float(tide_data["predictions"][tide_data["predictions"].index(pred)+1]["v"])) or \
                       (prev_value > curr_value and curr_value < float(tide_data["predictions"][tide_data["predictions"].index(pred)+1]["v"])):
                        next_extreme = curr_value
                        next_extreme_time = pred["t"]
                        break
                    prev_value = curr_value
                
                if next_extreme is not None:
                    tide_type = "High tide" if next_extreme > current_tide else "Low tide"
                    # Convert next_extreme_time from "YYYY-MM-DD HH:MM" to Unix timestamp
                    next_time_parts = next_extreme_time.split()
                    date_parts = [int(x) for x in next_time_parts[0].split('-')]
                    time_parts = [int(x) for x in next_time_parts[1].split(':')]
                    next_time_timestamp = time.mktime((date_parts[0], date_parts[1], date_parts[2], 
                                                     time_parts[0], time_parts[1], 0, 0, 0, 0))
                    next_time = time_in_tz(next_time_timestamp, tz_offset, timeFormat).split()[1]  # Get just the time portion
                    tide_info = f"{current_tide:.1f}'"
                    tide_time = f"{next_time}"
                else:
                    tide_info = f"{current_tide:.1f}'"
        except Exception as e:
            print("Tide error:", e)
            pass

    graphics.set_update_speed(1)
    graphics.set_pen(15)
    graphics.clear()
    graphics.set_pen(0)

    
    # Pre-calculate all values
    local_time = time_in_tz(int(aprs_data["entries"][0]["time"]), tz_offset, timeFormat)
    temp = float(aprs_data["entries"][0]["temp"])
    if units == "F":
        temp = celsius_to_fahrenheit(temp)
    humidity = aprs_data["entries"][0]["humidity"]
    pressure = float(aprs_data["entries"][0]["pressure"])
    wind_speed = aprs_data["entries"][0]["wind_speed"]
    wind_direction = int(aprs_data["entries"][0]["wind_direction"])
    
    layout = config.get('layout', 'landscape')
    
    if layout == 'landscape':

        print("Rendering landscape layout")

        # Initialize y position
        y_pos = 3
        
        if not tide_info:
            y_pos += 15
        
        # Draw timestamp at top
        graphics.set_font("bitmap6")
        graphics.text(f"at {local_time}", 10, y_pos, wordwrap=WIDTH - 20, scale=1)
        y_pos += 8
        
        # Draw nickname
        graphics.text(nickname, 10, y_pos, wordwrap=WIDTH - 20, scale=4)
        y_pos += 34
        
        # Draw temperature, humidity, pressure
        graphics.set_font("bitmap8")
        graphics.text(f"{temp:.0f}{units.lower()} {humidity}% {pressure:.0f}mb", 10, y_pos, wordwrap=WIDTH - 20, scale=3)
        y_pos += 29
        
        # Draw wind info
        graphics.text(f"{wind_speed}m/s", 10, y_pos, wordwrap=WIDTH - 20, scale=3)
        draw_arrow(120, y_pos + 10, 18, wind_direction)
        y_pos += 29
        
        # Draw tide info if available
        if tide_info:
            graphics.text(f"{tide_info} {tide_type[0]}: {tide_time}", 10, y_pos, wordwrap=WIDTH - 20, scale=3)
            tide_graph_width = 24 * 4 
            tide_graph_height = 24 
            tide_x = WIDTH - tide_graph_width//2
            tide_y = HEIGHT - tide_graph_height//2
            draw_tides(tide_x, tide_y, tide_data, tide_graph_width, tide_graph_height)
    
    else:  # Portrait layout

        print("Rendering portrait layout")
        
        x_pos = WIDTH - 8  # Start from left side
        y_pos = 8  # Start from top
        
        # Draw all items using alternating label and value functions
        x_pos = drawLabel(local_time, x_pos, y_pos) + 3
        x_pos = drawLabel(nickname, x_pos, y_pos, scale=2)
        
        drawLabel("Temp", x_pos, y_pos)
        x_pos = drawLabel("Humidity", x_pos, y_pos + WIDTH//5)
        
        drawValue(f"{temp:.0f}{units.lower()}", x_pos, y_pos)
        x_pos = drawValue(f"{humidity}%", x_pos, y_pos + WIDTH//5)
        
        x_pos = drawLabel("Pressure", x_pos, y_pos)
        x_pos = drawValue(f"{pressure:.0f}mb", x_pos, y_pos)
        
        x_pos = drawLabel("Wind Speed", x_pos, y_pos)
        
        draw_arrow(x_pos - 10, HEIGHT - 14, 16, wind_direction)
        x_pos = drawValue(f"{wind_speed}m/s", x_pos, y_pos)
        
        # Draw tide info if available
        if tide_info:
            x_pos = drawLabel("Tide", x_pos, y_pos)
            x_pos = drawValue(tide_info, x_pos, y_pos)

            x_pos = drawLabel(tide_type, x_pos, y_pos)
            x_pos = drawValue(tide_time, x_pos, y_pos)
            # Draw smaller tide graph rotated 90 degrees
            tide_graph_width = HEIGHT / 4
            tide_graph_height = HEIGHT
            tide_x = tide_graph_width//2
            tide_y = tide_graph_height//2
            draw_tides(tide_x, tide_y, tide_data, tide_graph_width, tide_graph_height, rotation=90)
    
    graphics.update()









