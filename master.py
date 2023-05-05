import asyncio
from src import sx127x
from src import config_lora
from src import LoRaReceiver


async def main():
    controller = config_lora.Controller()
    lora = controller.add_transceiver(sx127x.SX127x(name='LoRa'),
                                      pin_id_ss=config_lora.Controller.PIN_ID_FOR_LORA_SS,
                                      pin_id_RxDone=config_lora.Controller.PIN_ID_FOR_LORA_DIO0)
    print('lora', lora)
    await LoRaReceiver.receive(lora)


asyncio.run(main())
