import asyncio
from chimera_core.core.manager.module import ModuleManager

from loguru import logger

from xoa_driver import enums

from chimera_core import controller, types
from chimera_core.core.manager.dataset import ModuleConfig


# TODO: Allow Valkirye and Chimera testers to being connected
# TODO: To create functions of configurring

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

    # will check if have chimera module or raise error
    logger.debug(await my_controller.add_tester(my_tester_credential))

    my_tester_info = await my_controller.list_testers()
    my_tester_info = my_tester_info[my_tester_credential.id]

    tester_manager = await my_controller.use(my_tester_credential, username='chimera-core', reserve=False)
    module = await tester_manager.use_module(0, reserve=False)
    port = await tester_manager.use_port(module_id=0, port_id=0, reserve=False)

    # read current config
    module_current_config = await module.config.get()
    logger.debug(module_current_config.comment)
    # await module.reserve_if_not()
    # module_current_config.comment = 'hello'
    # await module.config.set(module_current_config)
    module_current_config = await module.config.get()
    logger.debug(module_current_config.comment)

    # update config
    # module_current_config.comment = 'world'
    # await module.config.set(module_current_config)

    port_config = await port.config.get()
    # logger.debug(port_config)
    await port.reserve_if_not()
    port_config.emulate = enums.OnOff.ON
    # await port.config.set(port_config)

    flow = port.flows[1]
    await flow.shadow_filter.reset()
    basic_filter_mode = await flow.shadow_filter.use_basic_mode()
    current_filter_config = await basic_filter_mode.get()
    logger.debug(current_filter_config)

    current_filter_config.use_l2plus = enums.L2PlusPresent.VLAN1
    current_filter_config.vlan.use = enums.FilterUse.AND
    current_filter_config.vlan.action = enums.InfoAction.INCLUDE

    current_filter_config.vlan.use_tag_inner = enums.OnOff.ON
    current_filter_config.vlan.value_tag_inner = 20
    current_filter_config.vlan.mask_tag_inner = "0x0FFF"

    current_filter_config.vlan.use_pcp_inner = enums.OnOff.OFF
    current_filter_config.vlan.value_pcp_inner = 0
    current_filter_config.vlan.mask_pcp_inner = "0x07"

    current_filter_config.vlan.use_tag_outer = enums.OnOff.OFF
    current_filter_config.vlan.value_tag_inner = 20
    current_filter_config.vlan.mask_tag_inner = "0x0FFF"

    current_filter_config.vlan.use_pcp_inner = enums.OnOff.OFF
    current_filter_config.vlan.value_pcp_inner = 0
    current_filter_config.vlan.mask_pcp_inner = "0x07"

    await basic_filter_mode.set(current_filter_config)

    latency_jtter_config = await flow.latency_jitter.get()
    latency_jtter_config.constant_delay.delay = 1000000
    latency_jtter_config.schedule.duration = 10
    logger.debug(latency_jtter_config)
    await flow.latency_jitter.set(latency_jtter_config)
    return None

    drop_config = await flow.drop.get()
    drop_config.fixed_burst.burst_size = 100
    logger.debug(drop_config)
    await flow.drop.set(drop_config)
    await flow.drop.enable(True)

    await flow.shadow_filter.set()
    await flow.shadow_filter.enable(True)

    # await flow.latency_jitter.enable(True)
    # await flow.drop.enable(True)


    # chimera_session.fetch_statistics(p, use=True) # Add port for fetching statistics data from it
    # chimera_session.fetch_statistics(p, use=False) # remove port from fetching of the statistics
    # chimera_session.uselect_all_ports_from_statistics() # ?? need better name

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(main())
    loop.run_forever()
