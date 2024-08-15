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
  - phew [project page](https://github.com/pimoroni/phew)
  - urllib [project page](https://github.com/pfalcon/micropython-lib)

## Standing on the shoulders of giants
Large parts of this project were heavily inspired by ghubcoder and Simon Prickett – I'm very grateful to them for writing up and open sourcing their work!

Check out:
https://simonprickett.dev/wifi-setup-with-raspberry-pi-pico-w/
and
https://ghubcoder.github.io/posts/deep-sleeping-the-pico-micropython/
