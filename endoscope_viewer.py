# -*- coding: utf-8 -*-
"""
Experimental Python/OpenCV viewer for a non-UVC USB endoscope.

@author: Bognabon

Repository:
https://github.com/Bognabon/Endoscope_Viewer

Tested device:
  VID:PID  2ce3:3828
  IN EP    0x82
  OUT EP   0x02
  Format   320x240 YUY2/YUYV

Notes:
  The first video block contains a 512-byte preamble.
  Subsequent blocks start directly with a 153600-byte YUY2 frame.
"""

import struct
import time
from pathlib import Path

import cv2
import numpy as np
import usb.core
import usb.util


# =========================
# CONFIG
# =========================
VENDOR_ID = 0x2CE3
PRODUCT_ID = 0x3828

EP_IN = 0x82
EP_OUT = 0x02
INTERFACE = 0

WIDTH = 320
HEIGHT = 240
FRAME_SIZE = WIDTH * HEIGHT * 2  # YUY2/YUYV

# Read block:
# one 320x240 YUY2 frame plus a 512-byte preamble/extra block.
READ_SIZE = FRAME_SIZE + 512

# Leave as None on Linux / Raspberry Pi.
# On Windows, set this if PyUSB reports "No backend available", e.g.
# LIBUSB_PATH = r"C:\path\to\libusb-1.0.dll"
LIBUSB_PATH = None

SAVE_DIR = Path("captures")

DEBUG = True

WINDOW_NAME = "SuperCamera YUY2"
WINDOW_W = 640
WINDOW_H = 480


def find_camera():
    if LIBUSB_PATH:
        from usb.backend import libusb1

        backend = libusb1.get_backend(
            find_library=lambda x: LIBUSB_PATH
        )

        if backend is None:
            raise RuntimeError(
                f"Could not load libusb backend from {LIBUSB_PATH}"
            )

        return usb.core.find(
            idVendor=VENDOR_ID,
            idProduct=PRODUCT_ID,
            backend=backend,
        )

    return usb.core.find(
        idVendor=VENDOR_ID,
        idProduct=PRODUCT_ID,
    )


def detach_kernel_driver_if_needed(dev):
    try:
        if dev.is_kernel_driver_active(INTERFACE):
            print("Detaching kernel driver")
            dev.detach_kernel_driver(INTERFACE)
    except (NotImplementedError, usb.core.USBError):
        pass


def main():
    SAVE_DIR.mkdir(exist_ok=True)

    # =========================
    # USB SETUP
    # =========================
    print("Python is", struct.calcsize("P") * 8, "bit")

    dev = find_camera()

    if dev is None:
        raise RuntimeError("Camera not found")

    print("Device found")

    detach_kernel_driver_if_needed(dev)

    try:
        dev.set_configuration()
        print("Configuration set")
    except usb.core.USBError as e:
        print("set_configuration warning:", e)

    try:
        usb.util.claim_interface(dev, INTERFACE)
        print("Interface claimed")
    except usb.core.USBError as e:
        print("claim_interface warning:", e)

    for ep in [EP_IN, EP_OUT]:
        try:
            dev.clear_halt(ep)
            print(f"Cleared halt 0x{ep:02x}")
        except Exception as e:
            print(f"Could not clear halt 0x{ep:02x}:", e)

    # =========================
    # GETINFO
    # =========================
    print("Sending getinfo()")

    try:
        info = bytes(dev.ctrl_transfer(
            bmRequestType=0xA0,
            bRequest=0x00,
            wValue=0x0005,
            wIndex=0x0000,
            data_or_wLength=512,
            timeout=1000,
        ))

        print("getinfo length:", len(info))
        print("getinfo first 64 bytes:", info[:64].hex(" "))
        print(
            "getinfo ASCII:",
            ''.join(chr(b) if 32 <= b < 127 else "." for b in info[:64])
        )

    except usb.core.USBError as e:
        print("getinfo error:", e)

    # =========================
    # CAMERA UP
    # =========================
    print("Sending camera_up()")

    try:
        ret = dev.ctrl_transfer(
            bmRequestType=0x20,
            bRequest=0x01,
            wValue=0x0005,
            wIndex=0x0000,
            data_or_wLength=bytearray(64),
            timeout=1000,
        )
        print("camera_up returned:", ret)
    except usb.core.USBError as e:
        print("camera_up error:", e)

    time.sleep(0.2)

    # =========================
    # LIVE STREAM
    # =========================
    print("Starting live stream")
    print("Keys: q = quit, s = save frame")

    frame_count = 0
    save_count = 0
    first_video_block = True

    cv2.destroyAllWindows()

    cv2.namedWindow(
        WINDOW_NAME,
        cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO
    )

    try:
        while True:
            try:
                block = bytes(dev.read(EP_IN, READ_SIZE, timeout=3000))

            except usb.core.USBTimeoutError:
                continue

            except usb.core.USBError as e:
                print("USB error:", e)

                if e.errno == 32:
                    try:
                        dev.clear_halt(EP_IN)
                        print("Cleared halt on EP_IN")
                        continue
                    except Exception:
                        break

                break

            if not block:
                continue

            # The first successful block seems to contain a 512-byte preamble.
            if first_video_block:
                offset = 512
                first_video_block = False
            else:
                offset = 0

            if DEBUG and frame_count < 10:
                print(
                    "block", frame_count,
                    "len", len(block),
                    "offset", offset,
                    "first16", block[:16].hex(" ")
                )

            if len(block) < offset + FRAME_SIZE:
                print(
                    "Short block:",
                    len(block),
                    "needed:",
                    offset + FRAME_SIZE,
                    "skipping"
                )
                continue

            raw_frame = block[offset:offset + FRAME_SIZE]

            try:
                yuv = np.frombuffer(raw_frame, dtype=np.uint8).reshape(
                    (HEIGHT, WIDTH, 2)
                )
                img = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_YUY2)

            except Exception as e:
                print("Decode error:", e)
                continue

            frame_count += 1

            display = cv2.resize(
                img,
                (WINDOW_W, WINDOW_H),
                interpolation=cv2.INTER_NEAREST
            )

            cv2.imshow(WINDOW_NAME, display)

            # Do this after imshow, especially on Raspberry Pi/Linux.
            if frame_count == 1:
                cv2.resizeWindow(WINDOW_NAME, WINDOW_W, WINDOW_H)

            cv2.setWindowTitle(
                WINDOW_NAME,
                f"frame {frame_count} | block len {len(block)} | offset {offset}"
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                raise KeyboardInterrupt

            elif key == ord("s"):
                filename = SAVE_DIR / f"frame_{save_count:04d}.png"
                cv2.imwrite(str(filename), img)
                print("Saved", filename)
                save_count += 1

    except KeyboardInterrupt:
        print("Stopping")

    finally:
        cv2.destroyAllWindows()

        # Optional camera_down, matching Android
        try:
            print("Sending camera_down()")
            dev.ctrl_transfer(
                bmRequestType=0x20,
                bRequest=0x02,
                wValue=0x0005,
                wIndex=0x0000,
                data_or_wLength=bytearray(0),
                timeout=1000,
            )
        except Exception as e:
            print("camera_down warning:", e)

        try:
            usb.util.release_interface(dev, INTERFACE)
        except Exception:
            pass

        usb.util.dispose_resources(dev)
        print("Done")


if __name__ == "__main__":
    main()