import os
from dotenv import load_dotenv
from . import amqp_controller
import RPi.GPIO as GPIO
from time import sleep
from . import lcd_i2c
import json
from . import ascon
import binascii
import time
from . import config

load_dotenv()

display = lcd_i2c.lcd()
asc = ascon.Ascon()
rabbitmq_server = os.getenv('RABBITMQ_SERVER')
amqp_connection = amqp_controller.AMQPConnection(rabbitmq_server)
master_node = 'raspi'
node_one = 'esp32'

key_g = config.ENCRYPT_KEY
nonce_g = config.ENCRYPT_NONCE


async def receive(lora):
    msg_count = 0
    # display.lcd_clear()
    await connect_to_rabbitmq(amqp_connection)
    delay_ms = 4000
    previous_time = int(round(time.time() * 1000))
    # secs = 0
    while True:
        try:
            current_time = int(round(time.time() * 1000))
            elapsed_time = current_time - previous_time
            if elapsed_time >= delay_ms:
                mes_dict = {
                    "idp": msg_count,
                    "id": master_node,
                    "to": node_one
                }
                if msg_count == 0:
                    mes_dict["rst"] = "reset"
                mes_json = json.dumps(mes_dict)
                lora.println(mes_json)
                msg_count += 1
                print(f"send: {mes_json}\n")
                previous_time = current_time
            await on_receive(lora)
        except Exception as e:
            print(f"Error: {e}")

    # print("LoRa Receiver")
    # display.lcd_clear()
    # display.lcd_display_string("waiting lora", 1)
    # print("waiting lora")
    # try:
    #     while True:
    #         if lora.receivedPacket():
    #             lora.blink_led()
    #             try:
    #                 payload = lora.read_payload()
    #                 payload_decode = payload.decode('utf-8')
    #                 payload_ascii = payload_decode.encode('ascii')
    #                 plaintext, nonce = decryption(
    #                     asc, binascii.unhexlify(payload_ascii), key, nonce, "CBC")
    #                 message = plaintext.decode("utf-8")
    #                 message_json = json.loads(message)
    #                 show_info(display, message_json)
    #                 print("\n*** Received message ***\n{}".format(message))
    #                 print("with RSSI: {}\n".format(lora.packetRssi()))
    #                 await amqp_connection.send_amqp_message(payload)
    #             except Exception as e:
    #                 print(e)
    # except KeyboardInterrupt:
    #     display.lcd_clear()
    #     print("Keyboard interrupt detected.")
    #     await amqp_connection.close()
    #     display.lcd_display_string("closing", 1)
    #     display.lcd_display_string("goodbye...", 2)
    #     sleep(5)
    #     display.lcd_clear()


def receive_callback(lora):
    global nonce_g
    lora.blink_led()
    payload = lora.read_payload()
    # print(payload)
    # payload_decode = payload.decode('utf-8')
    # payload_ascii = payload_decode.encode('ascii')
    plaintext, nonce_g = decryption(
        asc, payload, key_g, nonce_g, "CBC")
    message_json = plaintext.decode("utf-8")
    message_dict = json.loads(message_json)
    show_info(display, message_dict)
    print("\n*** Received message ***\n{}".format(message_dict))
    print("with RSSI: {}\n".format(lora.packetRssi()))
    return message_dict, payload


async def on_receive(lora):
    if lora.receivedPacket():
        payload, ciphertext = receive_callback(lora)
        if not len(payload):
            return
        recipient = payload["to"]
        sender = payload["id"]
        if recipient != node_one and recipient != master_node:
            return
        if sender == node_one:
            await amqp_connection.send_amqp_message(ciphertext)


async def connect_to_rabbitmq(amqp_connection):
    while True:
        try:
            print("Connecting...")
            display.lcd_clear()
            display.lcd_display_string("Connecting to", 1)
            display.lcd_display_string("RabbitMQ Broker", 2)
            await amqp_connection.connect()
            print("Connected to RabbitMQ Broker")
            sleep(1)
            display.lcd_clear()
            display.lcd_display_string("Connected to", 1)
            display.lcd_display_string("RabbitMQ broker", 2)
            sleep(1)
            break
        except Exception as e:
            print(e)
            display.lcd_clear()
            show_on_lcd()
            display.lcd_display_string("Error, wait 1s", 1)
            display.lcd_display_string("Connecting...", 2)
            sleep(5)


def show_info(message_json):
    # display.lcd_clear()
    th = f'T: {message_json["t"]}C H: {message_json["h"]}%'
    # time = f'{get_formatted_date(message_json["tsp"])}'
    # display.lcd_display_string(time, 1)
    display.lcd_display_string(th, 2)


def show_on_lcd(items, delay=0):
    for x, text in enumerate(items):
        display.lcd_display_string(text, x+1)
    sleep(delay)


def get_formatted_date(date_tuple):
    return f"{date_tuple[0]:04d}-{date_tuple[1]:02d}-{date_tuple[2]:02d} {date_tuple[4]:02d}:{date_tuple[5]:02d}"


def decryption(ascon, ciphertext, key, nonce, mode="ECB"):
    # print(f"key: {key} len: {len(key)}")
    # print(f"nonce: {nonce} len: {len(nonce)}")
    plaintext = ascon.ascon_decrypt(
        key, nonce, associateddata=b"", ciphertext=ciphertext,  variant="Ascon-128")
    if mode == "CBC":
        new_nonce = ciphertext[:16]
        # print(f"nw: {new_nonce} len: {len(new_nonce)}")
    return plaintext, new_nonce
