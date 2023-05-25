import asyncio
from typing import Callable, Coroutine, Generator, Optional
from chimera_core.controller import MainController
from chimera_core.types import dataset
from chimera_core.types import distributions


class CoreExample:
    credential: dataset.Credentials
    controller: MainController

    def __init__(self, credential: dataset.Credentials):
        self.credential = credential
        self.tester: Optional[dataset.TesterManager] = None

    async def init_resources(self) -> None:
        self.controller = await MainController()
        await self.controller.add_tester(self.credential)
        self.tester = await self.controller.use(self.credential, username='chimera-core-example', reserve=False, debug=False)

    async def flow_configuration(self, flow: dataset.FlowManager) -> None:
        await flow.shadow_filter.clear()
        await flow.shadow_filter.init()
        flow_config = await flow.get()
        flow_config.comment = "On VLAN 20"
        await flow.set(flow_config)
        basic_filter = await flow.shadow_filter.use_basic_mode()
        basic_filter_config = await basic_filter.get()
        ethernet = basic_filter_config.layer_2.use_ethernet()
        ethernet.src_addr.off()
        ethernet.src_addr.off()
        # vlan_tag = basic_filter_config.layer_2_plus.use_1_vlan_tag()
        # vlan_tag.include()
        # vlan_tag.tag_inner.on(value=20, mask="0FFF")
        # vlan_tag.pcp_inner.off()
        # vlan_tag.tag_outer.off()
        # vlan_tag.pcp_inner.off()
        await basic_filter.set(basic_filter_config)
        await flow.shadow_filter.enable()
        await flow.shadow_filter.apply()

        drop_config = await flow.drop.get()
        fixed_burst = distributions.distribution_options_drop.FixedBurst(burst_size=5)
        fixed_burst.repeat(5)
        drop_config.set_distribution(fixed_burst)
        await flow.drop.start(drop_config)

        latency_jitter_config = await flow.latency_jitter.get()
        constant_delay = distributions.distribution_options_latency_jitter.ConstantDelay(delay=100000)
        latency_jitter_config.set_distribution(constant_delay)
        await flow.latency_jitter.start(latency_jitter_config)


    async def configuration(self):
        if not self.tester:
            await self.init_resources()
        assert self.tester
        port = await self.tester.use_port(module_id=2, port_id=3, reserve=False)
        await port.reserve_if_not()
        port_config = await port.config.get()
        port_config.set_emulate_on()
        await port.config.set(port_config)
        flow_one = port.flows[1]
        await self.flow_configuration(flow_one)

    async def stop(self) -> None:
        ...

    async def start(self) -> None:
        ...

    async def collect_data(self) -> None:
        ...

async def main() -> None:
    credential = dataset.Credentials(
        product=dataset.EProductType.CHIMERA,
        host='127.0.0.1',
        port=12345,
    )
    example = CoreExample(credential)
    await example.configuration()
    await example.start()
    await example.collect_data()
    await example.stop()


if __name__ == "__main__":
    asyncio.run(main())