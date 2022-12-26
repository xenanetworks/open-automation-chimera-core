import asyncio

from loguru import logger
from xoa_driver import enums

from chimera_core import controller, types


TESTER_IP_ADDRESS = '192.168.1.201'


async def subscribe(my_controller: controller.MainController, pipe: str) -> None:
    async for msg in my_controller.listen_changes(pipe):
        logger.debug(msg)


async def main():
    my_controller = await controller.MainController()
    asyncio.gather(*[
        asyncio.create_task(subscribe(my_controller, types.PIPE_STATISTICS)),
        asyncio.create_task(subscribe(my_controller, types.PIPE_RESOURCES)),
    ])

    my_tester_credential = types.Credentials(
        product=types.EProductType.CHIMERA,
        host=TESTER_IP_ADDRESS,
    )

    await my_controller.add_tester(my_tester_credential)
    my_tester_info = await my_controller.list_testers()
    my_tester_info = my_tester_info[my_tester_credential.id]

    tester_manager = await my_controller.use(my_tester_credential, username='chimera-core', reserve=False)
    module = await tester_manager.use_module(module_id=0, reserve=False)
    port = await tester_manager.use_port(module_id=0, port_id=0, reserve=False)

    module_current_config = await module.config.get()
    module_current_config.comment = 'new comment'
    await module.reserve_if_not()
    await module.config.set(module_current_config)
    module_current_config = await module.config.get()

    port_config = await port.config.get()
    await port.reserve_if_not()
    port_config.emulate = enums.OnOff.ON
    await port.config.set(port_config)

    flow = port.flows[1]
    await flow.shadow_filter.reset()
    basic_filter_mode = await flow.shadow_filter.use_basic_mode()  # or use_extend_mode()
    current_filter_config = await basic_filter_mode.get()
    logger.debug(current_filter_config)

    current_filter_config.use_l2plus = enums.L2PlusPresent.VLAN1
    current_filter_config.vlan.use = enums.FilterUse.AND
    current_filter_config.vlan.action = enums.InfoAction.INCLUDE

    current_filter_config.vlan.tag_inner.on(value=20, mask="0FFF")


    current_filter_config.vlan.use_pcp_inner = enums.OnOff.OFF
    current_filter_config.vlan.value_pcp_inner = 0
    current_filter_config.vlan.mask_pcp_inner = "0x07"

    current_filter_config.vlan.use_tag_outer = enums.OnOff.OFF

    current_filter_config.vlan.use_pcp_inner = enums.OnOff.OFF
    current_filter_config.vlan.value_pcp_inner = 0
    current_filter_config.vlan.mask_pcp_inner = "0x07"

    await basic_filter_mode.set(current_filter_config)
    await flow.shadow_filter.enable(True)

    latency_jtter_config = await flow.latency_jitter.get()
    logger.debug(latency_jtter_config)
    latency_jtter_config.constant_delay.delay = 1000000
    latency_jtter_config.schedule.duration = 2
    latency_jtter_config.schedule.period = 0
    await flow.latency_jitter.set(latency_jtter_config)
    await flow.latency_jitter.enable(True)

    drop_config = await flow.drop.get()
    logger.debug(drop_config)
    drop_config.fixed_burst.burst_size = 100
    drop_config.schedule.duration = 2
    drop_config.schedule.period = 5
    await flow.drop.set(drop_config)
    await flow.drop.enable(True)


    # chimera_session.fetch_statistics(p, use=True) # Add port for fetching statistics data from it
    # chimera_session.fetch_statistics(p, use=False) # remove port from fetching of the statistics
    # chimera_session.uselect_all_ports_from_statistics() # ?? need better name

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(main())
    loop.run_forever()
