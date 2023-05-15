import asyncio
from src import sx127x
from src import config_lora
from src import LoRaReceiver
from dotenv import load_dotenv
from src import lcd_i2c

load_dotenv()

display_master = lcd_i2c.lcd()
controller = config_lora.Controller()
lora = controller.add_transceiver(sx127x.SX127x(name='LoRa'),
                                  pin_id_ss=config_lora.Controller.PIN_ID_FOR_LORA_SS,
                                  pin_id_RxDone=config_lora.Controller.PIN_ID_FOR_LORA_DIO0)


async def main():
    try:
        print('lora', lora)
        await LoRaReceiver.receive(lora)
    except Exception as e:
        print(e)

asyncio.run(main())
