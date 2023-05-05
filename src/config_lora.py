import sys
import os
import time


IS_PC = False
IS_MICROPYTHON = (sys.implementation.name == 'micropython')
IS_ESP8266 = (os.uname().sysname == 'esp8266')
IS_ESP32 = (os.uname().sysname == 'esp32')
IS_TTGO_LORA_OLED = None
IS_RPi = not (IS_MICROPYTHON or IS_PC)


def mac2eui(mac):
    mac = mac[0:6] + 'fffe' + mac[6:]
    return hex(int(mac[0:2], 16) ^ 2)[2:] + mac[2:]


if IS_RPi:

    # Node Name
    import socket
    NODE_NAME = 'RPi_' + socket.gethostname()

    # millisecond
    def millisecond(): return time.time() * 1000

    # Controller
    from .controller_rpi import Controller
