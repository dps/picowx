# picowx
_An APRS radio powered raspberry pi pico-w weather station_.
Uses the aprs.fi API via your WiFi network to display weather reports transmitted via the [Automatic Packet Reporting System](https://en.wikipedia.org/wiki/Automatic_Packet_Reporting_System) – local weather that's often not available via popular weather APIs. Simple captive-portal configuration UI and tuned for low power standby.

![image](https://github.com/user-attachments/assets/5d429ddd-7e61-4307-9d12-4549a66b179d)

## Hardware
- Raspberry Pi Pico-W
- Pimoroni Inky Pack
- Pimoroni LiPo shim and battery (optional)
- 0.1" headers for pico-w, you'll need to solder these on (or buy a pico-wh with pre-soldered headers)
  
[digikey parts list, minus battery](https://www.digikey.com/en/mylists/list/2R079622OC)

## Software
Most of the logic is implemented in micropython, but the dormant sleep mode requires custom C code. I've built a special version of pimoroni flavor micropython to add this functionality. You can find a flashable .uf2 file in this repo and look or tiner with the micropython changes directly in https://github.com/dps/micropython. https://github.com/dps/pimoroni-pico is a fork of pimoroni's micropython (with support for Inky pack) which pulls in my custom micropython and has a Github action / continuous build which produced that .uf2 file should you wish to reproduce it yourself.

## User guide

### Installation
- Clone the repo
- Flash the .uf2 file (hold down the bootsel button while plugging your pico-w into your computer, then copy the .uf2 file to the mass storage volume that appears).
- Copy the py and html files in this repo to the board using Thonny
- Install the following dependencies via Thonny's Tools...Manage Plugins... menu
  - phew [project page](https://github.com/pimoroni/phew) micropython_phew-0.0.3
  - urllib [project page](https://github.com/pfalcon/micropython-lib) micropython_urllib.urequest-0.6.3
    - edit `urequest.py` to `import ssl` instead of `import ussl` 
- Reboot, configuration mode will start

### Configuration mode
Your device will render a UI like this:
<img width="610" alt="Screenshot 2024-08-14 at 6 09 47 PM" src="https://github.com/user-attachments/assets/4019f52e-37d3-422e-8fa0-44b3cbd1929b">
Use your phone or computer to connect to the `picowx` wifi network. A captive portal config UI should appear. If it doesn't, open your web browser and navigate to `http://neverssl.com` (always a good trick!).

You'll see a screen like this:
<img width="610" alt="Screenshot 2024-08-14 at 6 27 49 PM" src="https://github.com/user-attachments/assets/9604ecde-8076-4514-92b6-ea8f6bde2b87">

Enter the wifi network name and password that you'd like your device to connect to. The station callsign for the weather station you'd like to track can be found via https://aprs.fi/.

<img width="1238" alt="Screenshot 2024-08-14 at 6 29 45 PM" src="https://github.com/user-attachments/assets/197f57cf-b399-40d3-8a88-3bf5ce674dd9">
aprs.fi shows, by default, the stations near your current location - choose any one marked as a `WX` (weather reporting) station and enter its callsign in the config ui.


Next, you'll need an aprs.fi API key. Create an account on `aprs.fi` and then you'll find this at https://aprs.fi/account/ 
<img width="412" alt="Screenshot 2024-08-14 at 7 33 18 PM" src="https://github.com/user-attachments/assets/13d22d84-9f5f-4bf7-96aa-79cb75caf867">

The aprs.fi API has a number of [terms](https://aprs.fi/page/api), which this project complies with, but do keep them in mind if you're making any modifications.

Optionally, you can add a station nickname, which will be displayed in the UI instead of the callsign and your timezone offset in hours to UTC (e.g. `-7` for PST) if you'd like to see updated times in your local timezone. If you leave this empty, you'll see updated times in UTC.

Finally, save your config and you'll see a page a bit like this:

<img width="473" alt="Screenshot 2024-08-14 at 7 39 11 PM" src="https://github.com/user-attachments/assets/06074203-49e0-4d41-86d4-21e6f6fa9488">

<img width="414" alt="Screenshot 2024-08-14 at 7 39 48 PM" src="https://github.com/user-attachments/assets/36be99cf-3a75-440d-8f3e-3a9898419507">

### Application mode
Once configured, picowx will connect to the configured network, download the latest weather report for the station you set up, display it on the eInk screen and then go to sleep.

You can refresh the display at any time by pressing button A on the Inky Pack.



https://github.com/user-attachments/assets/94a6b6dc-041e-45d1-a4c0-5800111ca9b5

## Power consumption

By using `sleep_goto_dormant_until_pin` from `pico-extras`, this project consumes about 1.4mA when asleep.

![IMG_9603](https://github.com/user-attachments/assets/80096b62-8fb8-4fd5-bd53-1b19cc422e17)

Power consumption verified via my very low-fi multimeter setup.

## Standing on the shoulders of giants
Large parts of this project were heavily inspired by ghubcoder and Simon Prickett – I'm very grateful to them for writing up and open sourcing their work!

Check out:
https://simonprickett.dev/wifi-setup-with-raspberry-pi-pico-w/
and
https://ghubcoder.github.io/posts/deep-sleeping-the-pico-micropython/

I'm also very grateful to the [maintainers of aprs.fi](https://aprs.fi/page/credits) - it's a great service with a very intuitive API.
