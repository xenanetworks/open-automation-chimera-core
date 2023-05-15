import asyncio

from loguru import logger

from chimera_core import controller, types
from chimera_core.core.manager.flow.distributions.drop import FixedBurst
from chimera_core.core.manager.flow.distributions.latency_jitter import ConstantDelay
from chimera_core.core.manager.flow.shadow_filter.__dataset import ProtocolSegement


TESTER_IP_ADDRESS = '127.0.0.1'


async def subscribe(my_controller: controller.MainController, pipe: str) -> None:
    async for msg in my_controller.listen_changes(pipe):
        logger.debug(msg)


async def main():
    my_controller = await controller.MainController()
    asyncio.gather(*[
        asyncio.create_task(subscribe(my_controller, types.PIPE_STATISTICS)),
    ])

    my_tester_credential = types.Credentials(
        product=types.EProductType.CHIMERA,
        host=TESTER_IP_ADDRESS,
        port=12345,
    )

    await my_controller.add_tester(my_tester_credential)
    my_tester_info = await my_controller.list_testers()
    my_tester_info = my_tester_info[my_tester_credential.id]

    tester_manager = await my_controller.use(my_tester_credential, username='chimera-core', reserve=False, debug=False)
    port = await tester_manager.use_port(module_id=2, port_id=3, reserve=False)
    port_config = await port.config.get()
    logger.debug(port_config)
    await port.reserve_if_not()
    port_config.set_emulate_on()
    await port.config.set(port_config)
    flow = port.flows[1]

    await flow.shadow_filter.reset()

    # extended mode
    # extend_filter_mode = await flow.shadow_filter.use_extended_mode()
    # config = await extend_filter_mode.get()
    # logger.debug(config)

    # config.protocol_segments = config.protocol_segments[:2]
    # len(config.protocol_segments)

    # ethernet = ProtocolSegement(
    #     protocol_type=enums.ProtocolOption.ETHERNET,
    #     value='000001111',
    #     mask='1110000',
    # )
    # ipv41 = ProtocolSegement(
    #     protocol_type=enums.ProtocolOption.IP,
    #     value='000001111',
    #     mask='1110000',
    # )
    # ipv42 = ProtocolSegement(
    #     protocol_type=enums.ProtocolOption.IP,
    #     value='000001111',
    #     mask='1110000',
    # )
    # config.protocol_segments = (ethernet,ipv41,ipv42)

    # # await extend_filter_mode.set(config)
    # # config = await extend_filter_mode.get()
    # # logger.debug(config)
    # end of extended mode

    basic_filter_mode = await flow.shadow_filter.use_basic_mode()
    current_filter_config = await basic_filter_mode.get()
    logger.debug(current_filter_config)

    ipv4 = current_filter_config.layer_3.use_ipv4()
    ipv4.dest_addr.on(address='8.8.8.8', mask='FFFF')
    ipv4.include()
    await basic_filter_mode.set(current_filter_config)

    # drop_config = await flow.drop.get()
    # logger.debug(drop_config)
    # fixed_burst = FixedBurst()
    # fixed_burst.repeat(2)
    # fixed_burst.repeat(period=100)
    # drop_config.set_distribution(fixed_burst)
    # await flow.drop.set(drop_config)

    latency_jtter_config = await flow.latency_jitter.get()
    logger.debug(latency_jtter_config)
    constant_delay = ConstantDelay(delay=100)
    latency_jtter_config.set_distribution(constant_delay)
    await flow.latency_jitter.start(latency_jtter_config)
    await flow.shadow_filter.enable(True)


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(main())
    loop.run_forever()
