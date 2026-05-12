# SuperCamera / Geek-Szitman USB Endoscope Python Viewer
Experimental Python/OpenCV viewer for a non-UVC USB endoscope camera.
Viewing the live video feed from a cheap USB Endoscope with the name “SuperCamera”/Geek-Szitman.
This is an experimental Python viewer for a non-UVC USB endoscope sold under various “SuperCamera”/Geek-Szitman-style names. 
It was pulled together from observed USB behaviour, and is only known to work with devices exposing VID:PID 2ce3:3828 with bulk endpoints 0x82/0x02.

## Tested platforms (in May 2026)
- Windows 11 PC
- Raspberry Pi 5

## Note about resolution
This camera is marketed as “1920 HD”, suggesting a still-image resolution around 1920 × 1440. When used with a phone app, saved images may indeed report this resolution, but this appears to be upsampled rather than the native stream resolution.
The raw video stream decoded by this script is 320 × 240 YUY2/YUYV. This may be too low for many applications, especially where fine detail is required.

## Tested device
- VID:PID: 2ce3:3828
- Reported/marketed as Geek/Szitman/SuperCamera-style endoscope
- Interface: 0
- Bulk IN: 0x82
- Bulk OUT: 0x02
- Actual decoded stream: 320x240 YUY2/YUYV
- Purchased single-lens 5m cable variant from amazon: https://www.amazon.co.uk/dp/B0CZHT2VHS/?coliid=I1HCGW7DOA3MOP&colid=1VVKZQ9NPBSBT&ref_=list_c_wl_lv_ov_lig_dp_it&th=1 with item name: Endoscope Inspection Camera, Ennovor 1920 HD Flexible Rigid Snake Inspection Camera, 8 LED Lights No WiFi Endoscope, IP67 Waterproof Sink Pipe Drain Borescope, Android iOS (Single-lens 5m)

<p>
  <img src="docs/images/Endoscope_camera.jpeg" alt="Endoscope camera" width="45%">
  <img src="docs/images/Endoscope_camera_box.jpeg" alt="Endoscope camera box" width="45%">
</p>

## What this does
- Sends getinfo control transfer
- Sends camera_up control transfer
- Reads Android-style 154112-byte blocks
- Decodes 153600-byte frames as 320x240 YUY2
- Displays live video using OpenCV
- Can save PNG frames

## Requirements
- Python 3
- pyusb
- opencv-python
- numpy
- libusb
- On Linux/Raspberry Pi: appropriate USB permissions or sudo
- On Windows: WinUSB/libusb driver via Zadig and libusb-1.0.dll

## Usage
python endoscope_viewer.py

## Notes
- First video block uses offset 512
- Later blocks use offset 0
- Not a UVC webcam
- Other devices may differ

## Windows note
- On Windows, PyUSB may need access to `libusb-1.0.dll`. Download/install a matching 64-bit libusb build if using 64-bit Python, and either place it somewhere on your PATH or edit `LIBUSB_PATH` in the script.
- You may also need to use Zadig to bind the camera interface to WinUSB/libusb.
- On Windows, if PyUSB reports "No backend available", set `LIBUSB_PATH` to the path of a local `libusb-1.0.dll`.

## Disclaimer
Experimental, no warranty, use at your own risk.
