import asyncio

from loguru import logger

from chimera_core import controller, types
from chimera_core.core.session.dataset import ModuleConfig


# TODO: Allow Valkirye and Chimera testers to being connected
# TODO: Only show Chimera modules in resources dataset
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

    # "session" can be a different name which represents current actions under an resource
    chimera_session = await my_controller.start_session(my_tester_credential)

    module = chimera_session.modules[0]
    module_current_config = await module.config.get()
    logger.debug(module_current_config)

    ######### ?? obj or params to update the config, need discuss ########

    # update by params
    await module.config.set(comment='hello')
    module_current_config = await module.config.get()
    logger.debug(module_current_config)

    # update by obj
    new_module_config = ModuleConfig(comment="world")
    await module.config.set(new_module_config)

    p = module.ports[0]
    flow = p.flows[0]
    current_cfg = await flow.latency_jitter.get()
    logger.debug(current_cfg)

    new_cfg = Config(delay=10000)
    await flow.latency_jitter.set(new_cfg)

    # # ... all other flow methods
    await flow.latency_jitter.enable(True)

    chimera_session.fetch_statistics(p, use=True) # Add port for fetching statistics data from it
    chimera_session.fetch_statistics(p, use=False) # remove port from fetching of the statistics
    chimera_session.uselect_all_ports_from_statistics() # ?? need better name

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(main())
    loop.run_forever()