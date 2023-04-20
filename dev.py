import asyncio


from loguru import logger
from xoa_driver import enums

from chimera_core import controller, types
from chimera_core.core.manager.dataset import FixedBurst, ProtocolSegement, ConstantDelay


TESTER_IP_ADDRESS = '127.0.0.1'


async def subscribe(my_controller: controller.MainController, pipe: str) -> None:
    async for msg in my_controller.listen_changes(pipe):
        logger.debug(msg)


async def main():
    my_controller = await controller.MainController()
    asyncio.gather(*[
        asyncio.create_task(subscribe(my_controller, types.PIPE_STATISTICS)),
        # asyncio.create_task(subscribe(my_controller, types.PIPE_RESOURCES)),
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
    port = await tester_manager.use_port(module_id=2, port_id=2, reserve=False)

    port_config = await port.config.get()
    await port.reserve_if_not()
    # port_config.emulate = enums.OnOff.ON
    # await port.config.set(port_config)

    flow = port.flows[2]

    # await flow.shadow_filter.reset()
    basic_filter_mode = await flow.shadow_filter.use_basic_mode()  # or use_extend_mode()
    current_filter_config = await basic_filter_mode.get()
    logger.debug(current_filter_config)

    drop_config = await flow.drop.get()
    logger.debug(drop_config)
    # fixed_burst = FixedBurst()
    # fixed_burst.repeat(period=2)
    # await flow.drop.apply(fixed_burst) # send config
    # drop_config.distribution.set_distribution(fixed_burst)
    # distribution = drop_config.distribution.get_current_distribution()
    # assert distribution is fixed_burst
    # await flow.drop.set(drop_config)
    # await flow.drop.start(True)

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
    await flow.shaper.start(shaper_config)

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(main())
    loop.run_forever()
