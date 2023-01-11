import asyncio

from loguru import logger
from xoa_driver import enums

from chimera_core import controller, types


TESTER_IP_ADDRESS = '87.61.110.118'


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
    module = await tester_manager.use_module(module_id=2, reserve=False)
    port = await tester_manager.use_port(module_id=2, port_id=3, reserve=False)

    module_current_config = await module.config.get()
    module_current_config.comment = 'new comment'
    # await module.reserve_if_not()
    # await module.config.set(module_current_config)
    # module_current_config = await module.config.get()

    port_config = await port.config.get()
    await port.reserve_if_not()
    port_config.emulate = enums.OnOff.ON
    await port.config.set(port_config)

    flow = port.flows[1]
    await flow.shadow_filter.reset()
    basic_filter_mode = await flow.shadow_filter.use_basic_mode()  # or use_extend_mode()
    current_filter_config = await basic_filter_mode.get()
    logger.debug(current_filter_config)

    # layer 2
    ethernet = current_filter_config.layer_2.use_ethernet()
    ethernet.src_addr.on(value='00FF1F9BBE95')
    ethernet.include()

    # layer 2 plus
    vlan = current_filter_config.layer_2_plus.use_1_vlan_tag()
    vlan.include()
    vlan.pcp_inner.off()
    vlan.tag_inner.on(value=20, mask="0FFF")
    vlan.pcp_outer.off()
    vlan.tag_outer.off()

    # layer 3
    ipv4 = current_filter_config.layer_3.use_ipv4()
    ipv4.src_addr.on(value='192.168.1.160')
    ipv4.dest_addr.on(value='192.168.1.161')
    ipv4.include()

    # layer 4
    tcp = current_filter_config.layer_4.use_tcp()
    tcp.src_port.on(value=443, mask='ffff')
    tcp.include()

    # layer xena
    tpld = current_filter_config.layer_xena.use_tpld()
    tpld.include()
    tpld_id_config = tpld.configs[0]  # from 0 to 16
    tpld_id_config.on(tpld_id=0)

    # layer any
    any_field = current_filter_config.layer_any.use_any_field()
    any_field.on(position=0, value='7F')
    any_field.include()

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
