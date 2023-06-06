import asyncio
from functools import partial
from typing import List

from loguru import logger

from chimera_core.controller import MainController
from chimera_core.types import dataset
from chimera_core.types import distributions


class CoreExample:
    credential: dataset.Credentials
    controller: MainController
    tester: dataset.TesterManager

    def __init__(self, credential: dataset.Credentials, module_id: int, port_id: int, flow_id: int, stop_event: asyncio.Event) -> None:
        self.credential = credential
        self.module_id = module_id
        self.port_id = port_id
        self.flow_id = flow_id
        self.stop_event = stop_event

    async def init_resources(self) -> None:
        self.controller = await MainController()
        tester_id = await self.controller.add_tester(self.credential)
        self.tester = await self.controller.use(tester_id, username='chimera-core-example', reserve=False, debug=False)
        self.__use_example_port = partial(self.tester.use_port, module_id=self.module_id, port_id=self.port_id)

    async def add_custom_distribution(self, linear: bool, data_x: List[int], comment: str) -> dataset.CustomDistribution:
        port = await self.__use_example_port(reserve=False)
        await port.reserve_if_not()
        cd = await port.custom_distributions.add(
            linear=linear,
            entry_count=len(data_x),
            data_x=data_x,
            comment=comment,
        )
        return cd

    async def configure_flow(self, flow: dataset.FlowManager) -> None:
        await flow.shadow_filter.clear()
        await flow.shadow_filter.init()
        # await flow.shadow_filter.apply()
        flow_config = await flow.get()
        flow_config.comment = "On VLAN 20"
        await flow.set(flow_config)
        basic_filter = await flow.shadow_filter.use_basic_mode()
        basic_filter_config = await basic_filter.get()
        ethernet = basic_filter_config.layer_2.use_ethernet()
        ethernet.src_addr.off()
        ethernet.src_addr.off()
        vlan_tag = basic_filter_config.layer_2_plus.use_1_vlan_tag()
        vlan_tag.include()
        vlan_tag.tag_inner.on(value=20, mask=dataset.Hex("0FFF"))
        vlan_tag.pcp_inner.off(value=0, mask=dataset.Hex("07"))
        vlan_tag.tag_outer.off(value=20, mask=dataset.Hex("0FFF"))
        vlan_tag.pcp_inner.off(value=0, mask=dataset.Hex("07"))
        await basic_filter.set(basic_filter_config)
        await flow.shadow_filter.enable()
        await flow.shadow_filter.apply()

        drop_config = await flow.drop.get()
        fixed_burst = distributions.drop.FixedBurst(burst_size=5) # short or long api
        fixed_burst.repeat(5)
        drop_config.set_distribution(fixed_burst)

        example_custom_distribution = await self.add_custom_distribution(
            linear=False,
            data_x=[0, 1] * 256,
            comment="Example Custom Distribution"
        )
        custom = distributions.drop.Custom(custom_distribution=example_custom_distribution)
        custom.repeat_pattern(duration=2, period=6)
        drop_config.set_distribution(custom)
        await flow.drop.start(drop_config)

        latency_jitter_config = await flow.latency_jitter.get()
        constant_delay = distributions.latency_jitter.ConstantDelay(delay=100000)
        latency_jitter_config.set_distribution(constant_delay)
        await flow.latency_jitter.start(latency_jitter_config)

    async def configure_resources(self) -> None:
        await self.init_resources()
        port = await self.__use_example_port(reserve=False)
        await port.reserve_if_not()
        flow_one = port.flows[self.flow_id]
        await self.configure_flow(flow_one)

    async def __use_flow(self, flow_id: int) -> dataset.FlowManager:
        port = await self.__use_example_port(reserve=True)
        flow = port.flows[flow_id]
        return flow

    async def start(self) -> None:
        await self.toggle_port_emulate(is_set_on=True)

    async def toggle_port_emulate(self, is_set_on: bool = False) -> None:
        port = await self.__use_example_port(reserve=True)
        port_config = await port.config.get()
        if is_set_on:
            port_config.set_emulate_on()
        else:
            port_config.set_emulate_off()
        await port.config.set(port_config)

    async def stop(self) -> None:
        await self.toggle_port_emulate(is_set_on=False)

    async def collect_data(self) -> None:
        flow = await self.__use_flow(self.flow_id)
        while not self.stop_event.is_set():
            rx = await flow.statistics.rx.total.get()
            drop = await flow.statistics.total.dropped.get()
            logger.debug(f"total received packet: {rx.packet_count}, total dropped: {drop.pkt_drop_count_total}")
            await asyncio.sleep(1)

async def main() -> None:
    credential = dataset.Credentials(
        product=dataset.EProductType.CHIMERA,
        host='127.0.0.1',
        port=12345,
    )
    stop_event = asyncio.Event()
    example = CoreExample(credential, module_id=2, port_id=3, flow_id=1, stop_event=stop_event)
    await example.configure_resources()
    await example.start()
    try:
        await example.collect_data()
    except KeyboardInterrupt:
        stop_event.set()
    await example.stop()


if __name__ == "__main__":
    asyncio.run(main())