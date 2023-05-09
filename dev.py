import asyncio

from loguru import logger
from xoa_driver import enums

from chimera_core import controller, types
from chimera_core.core.manager.flow.distributions.drop import FixedBurst


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
    module = await tester_manager.use_module(module_id=2, reserve=False)
    # await module.config.get()

    port = await tester_manager.use_port(module_id=2, port_id=2, reserve=False)

    port_config = await port.config.get()
    logger.debug(port_config)
    await port.reserve_if_not() # name temp
    port_config.set_emulate_on()
    await port.config.set(port_config)
    flow = port.flows[1]

    # await flow.shadow_filter.reset()
    extend_filter_mode = await flow.shadow_filter.use_extended_mode()
    config = await extend_filter_mode.get()
    logger.debug(config)

    config.protocol_segments = config.protocol_segments[:2]
    len(config.protocol_segments)

    ethernet = ProtocolSegement(
        protocol_type=enums.ProtocolOption.ETHERNET,
        value='000001111',
        mask='1110000',
    )
    ipv41 = ProtocolSegement(
        protocol_type=enums.ProtocolOption.IP,
        value='000001111',
        mask='1110000',
    )
    ipv42 = ProtocolSegement(
        protocol_type=enums.ProtocolOption.IP,
        value='000001111',
        mask='1110000',
    )
    config.protocol_segments = (ethernet,ipv41,ipv42)

    # await extend_filter_mode.set(config)
    # config = await extend_filter_mode.get()
    # logger.debug(config)

    # basic_filter_mode = await flow.shadow_filter.use_basic_mode()  # or use_extend_mode()
    # current_filter_config = await basic_filter_mode.get()
    # logger.debug(current_filter_config)

    # ipv4 = current_filter_config.layer_3.use_ipv4()
    # ipv4.dest_addr.on(address='8.8.8.8', mask='FFFF')
    # ipv4.include()
    # await basic_filter_mode.set(current_filter_config)

    drop_config = await flow.drop.get()

    logger.debug(drop_config)
    fixed_burst = FixedBurst()
    fixed_burst.repeat(period=2)
    drop_config.set_distribution(fixed_burst)
    return
    # await flow.drop.set(drop_config)
    # await flow.drop.stop()

    # fixed_burst = FixedBurst()
    # fixed_burst.one_shot()
    # mis_ordering_config = await flow.misordering.get()
    # mis_ordering_config.distribution.set_distribution(fixed_burst)
    # await flow.misordering.set(mis_ordering_config)
    # latency_jtter_config = await flow.latency_jitter.get()
    # logger.debug(latency_jtter_config)

    # constant_delay = ConstantDelay()
    # constant_delay.delay = 100000
    # latency_jtter_config.distribution.set_distribution(constant_delay)
    # corruption_config = await flow.corruption.get()
    # logger.debug(corruption_config)
    # latency_jtter_config.schedule.period = 0
    # await flow.latency_jitter.set(latency_jtter_config)
    # await flow.latency_jitter.enable(True)

    shaper_config = await flow.shaper.get()
    logger.debug(shaper_config)
    shaper_config.cbs = 12
    shaper_config.cir = 34
    shaper_config.buffer_size = 56
    await flow.shaper.set(shaper_config)
    await flow.shaper.start(shaper_config)

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(main())
    loop.run_forever()
