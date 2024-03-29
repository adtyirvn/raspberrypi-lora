import asyncio
from src import sx127x
from src import config_lora
from src import LoRaReceiver
import os
from dotenv import load_dotenv
from src import lcd_i2c

load_dotenv()

display_master = lcd_i2c.lcd()


async def main():
    display_master.lcd_clear()
    display_master.lcd_display_string("starting...", 1)
    print("starting...")
    controller = config_lora.Controller()
    lora = controller.add_transceiver(sx127x.SX127x(name='LoRa'),
                                      pin_id_ss=config_lora.Controller.PIN_ID_FOR_LORA_SS,
                                      pin_id_RxDone=config_lora.Controller.PIN_ID_FOR_LORA_DIO0)
    # print('lora', lora)
    await LoRaReceiver.receive(lora)

try:
    asyncio.run(main())
except Exception as e:
    print("Exit")
