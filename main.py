from phew import access_point, connect_to_wifi, is_connected_to_wifi, dns, server, ntp
from phew.template import render_template
import json
import machine
import network
import os
import utime
import time
import _thread
from picographics import PicoGraphics, DISPLAY_INKY_PACK
import picosleep
from aprs import aprs_update
from connect_ui import render_connect_ui, render_rebooting_ui


AP_NAME = "picowx"
AP_DOMAIN = "picowx.net"
AP_TEMPLATE_PATH = "ap_templates"
APP_TEMPLATE_PATH = "app_templates"
WIFI_FILE = "wifi.json"
WIFI_MAX_ATTEMPTS = 3
graphics = PicoGraphics(DISPLAY_INKY_PACK)
graphics.set_font("bitmap6")

IP_ADDR = ""

WIDTH, HEIGHT = graphics.get_bounds()


def machine_reset():
    utime.sleep(1)
    print("Resetting...")
    machine.reset()

def setup_mode():
    print("Entering setup mode...")
    render_connect_ui()
    
    def ap_index(request):
        if request.headers.get("host").lower() != AP_DOMAIN.lower():
            return render_template(f"{AP_TEMPLATE_PATH}/redirect.html", domain = AP_DOMAIN.lower())

        return render_template(f"{AP_TEMPLATE_PATH}/index.html")

    def ap_configure(request):
        print("Saving wifi credentials...")

        with open(WIFI_FILE, "w") as f:
            json.dump(request.form, f)
            f.close()

        render_rebooting_ui()
        # Reboot from new thread after we have responded to the user.
        _thread.start_new_thread(machine_reset, ())
        return render_template(f"{AP_TEMPLATE_PATH}/configured.html", ssid = request.form["ssid"])
        
    def ap_catch_all(request):
        if request.headers.get("host") != AP_DOMAIN:
            return render_template(f"{AP_TEMPLATE_PATH}/redirect.html", domain = AP_DOMAIN)

        return "Not found.", 404

    server.add_route("/", handler = ap_index, methods = ["GET"])
    server.add_route("/configure", handler = ap_configure, methods = ["POST"])
    server.set_callback(ap_catch_all)

    ap = access_point(AP_NAME)
    ip = ap.ifconfig()[0]
    dns.run_catchall(ip)
    # Start the web server...
    server.run()

def application_mode(config):
    ntp.fetch()    

    tz_offset = None if len(config['tz']) == 0 else int(config['tz'])
    nickname = config['callsign'] if len(config['nickname']) == 0 else config['nickname']

    # Update once and then on every button press
    while True:
        aprs_update(config['ssid'], config['password'], config['callsign'], config['api'], nickname, tz_offset)
        time.sleep(1)
        wlan = network.WLAN()
        wlan.active(False)
        wlan.deinit()
        button_a = machine.Pin(12, machine.Pin.IN, machine.Pin.PULL_UP)
        picosleep.pin(12, 1, 0)
        wlan.active(True)


# Figure out which mode to start up in...
try:
    os.stat(WIFI_FILE)

    # File was found, attempt to connect to wifi...
    with open(WIFI_FILE) as f:
        wifi_current_attempt = 1
        wifi_credentials = json.load(f)
        
        while (wifi_current_attempt < WIFI_MAX_ATTEMPTS):
           ip_address = connect_to_wifi(wifi_credentials["ssid"], wifi_credentials["password"])

           if is_connected_to_wifi():
               IP_ADDR = ip_address
               break
           else:
               wifi_current_attempt += 1
                
        if is_connected_to_wifi():
           application_mode(wifi_credentials)
        else:
           print("Bad wifi connection!")
           print(wifi_credentials)
           os.remove(WIFI_FILE)
           machine_reset()

except Exception as e:
    print(e)
    # Either no wifi configuration file found, or something went wrong, 
    # so go into setup mode.
    setup_mode()