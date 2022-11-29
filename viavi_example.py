import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Tuple, TypeVar
from xoa_driver.v2 import testers
from xoa_driver.v2 import modules
from xoa_driver.v2 import ports
from xoa_driver import utils
from xoa_driver.v2 import misc
from xoa_driver.enums import *

# region high-level functions

# --------------------------------------------------------------------------------------#
# function name: reserve_ports                                                          #
# This function takes care of port reservation procedure to simplify the user code.     #
#                                                                                       #
# This high-level function will be included in XOA HL Python                            #
# --------------------------------------------------------------------------------------#
async def reserve_ports(*used_ports: ports.GenericAnyPort) -> None:
    async def relinquish(port: ports.GenericAnyPort):
        print(port.info.reservation.name)
        if port.info.reservation == ReservedStatus.RESERVED_BY_OTHER:
            await port.reservation.set_relinquish()
            while port.info.reservation != ReservedStatus.RELEASED:
                await asyncio.sleep(0.01)
    await asyncio.gather(*[ relinquish(port) for port in used_ports ])
    await asyncio.gather(
        *[
            utils.apply(
                port.reservation.set_reserve(),
                port.reset.set()
            )
            for port in used_ports
        ]
    )

# --------------------------------------------------------------------------------------#
# function name: release_ports                                                          #
# This function resets and releases the ports                                           #
#                                                                                       #
# This high-level function will be included in XOA HL Python                            #
# --------------------------------------------------------------------------------------#
async def release_ports(*used_ports: ports.GenericAnyPort) -> None:
    coros = [
        utils.apply(
            port.reset.set(),
            port.reservation.set_release(),
        )
        for port in used_ports
    ]
    await asyncio.gather(*coros)

# endregion


# --------------------------------------------------------------------------------------#
# function name: safe_ports_usage                                                       #
# This function automatically reserve the ports you want to use,                        #
# and makes them into clean states after the use.                                       #
#                                                                                       #
# This high-level function will be included in XOA HL Python                            #
# --------------------------------------------------------------------------------------#
PT = TypeVar("PT", bound=ports.GenericAnyPort)

@asynccontextmanager
async def safe_ports_usage(*used_ports: PT) -> AsyncGenerator[Tuple[PT, ...], None]:
    await reserve_ports(*used_ports)
    try:
        yield used_ports
    finally:
        await release_ports(*used_ports)

async def flow_statistic_fetcher(flow: misc.ImpairmentFlow, stop_event: asyncio.Event) -> None:
    print(f"Start collecting statistics by Chimera...")
    count = 0
    while not stop_event.is_set():
        (rx, total_drop) = await utils.apply(
            flow.statistics.rx.total.get(),
            flow.statistics.total.dropped.get()
        )
        print(f"{count}\t\t\tChimera total received frames: {rx.packet_count},\t\ttotal dropped: {total_drop.pkt_drop_count_total}")
        count+=1
        await asyncio.sleep(1.0)


async def impairment_config(stop_event: asyncio.Event) -> None:

    # Access to the chassis that has a Chimera module in
    async with testers.L23Tester("192.168.1.201", "xena") as tester:
        # Access the module #10
        chimera_module = tester.modules.obtain(0)

        # Check whether the module is a Chimera module
        if not isinstance(chimera_module, modules.ModuleChimera):
            print("Selected not a Chimera module.", "Exiting.")
            return None

        # Auto reserving and cleaning the Chimera ports.
        async with safe_ports_usage(*chimera_module.ports) as reserved_chimera_ports:
            # Use port #0
            port_0 = reserved_chimera_ports[0]

            # Enable impairment on the port. If you don't do this, the port won't impair the incoming traffic.
            await port_0.emulate.set_on()

            # Use Flow #1 on this port. We will define a filter and configure impairment functions on it.
            flow_1 = port_0.emulation.flow[1]

            # Initializing the shadow copy of the filter. (If you don't know how Chimera impairment works, please read the Chimera's user manual)
            await flow_1.shadow_filter.initiating.set()
            # Basic mode
            await flow_1.shadow_filter.use_basic_mode()
            # Description of the flow
            await flow_1.comment.set("On VLAN 20")

            # Query the mode of the filter (either basic or extended)
            filter = await flow_1.shadow_filter.get_mode()

            # Set up the filter to impair frames with VLAN Tag = 20 (using command grouping)
            if isinstance(filter, misc.BasicImpairmentFlowFilter):
                await utils.apply(
                    filter.ethernet.settings.set(use=FilterUse.OFF, action=InfoAction.INCLUDE),
                    filter.ethernet.src_address.set(use=OnOff.OFF, value="0x000000000000", mask="0xFFFFFFFFFFFF"),
                    filter.ethernet.dest_address.set(use=OnOff.OFF, value="0x000000000000", mask="0xFFFFFFFFFFFF"),
                    filter.l2plus_use.set(use=L2PlusPresent.VLAN1),
                    filter.vlan.settings.set(use=FilterUse.AND, action=InfoAction.INCLUDE),
                    filter.vlan.inner.tag.set(use=OnOff.ON, value=20, mask="0x0FFF"),
                    filter.vlan.inner.pcp.set(use=OnOff.OFF, value=0, mask="0x07"),
                    filter.vlan.outer.tag.set(use=OnOff.OFF, value=20, mask="0x0FFF"),
                    filter.vlan.outer.pcp.set(use=OnOff.OFF, value=0, mask="0x07"),
                )

            # Enable the filter
            await flow_1.shadow_filter.enable.set_on()
            # Apply the filter so the configuration data in the shadow copy is committed to the working copy automatically.
            await flow_1.shadow_filter.apply.set()

            # Start configuring the impairment for the filter. (using command grouping)
            await utils.apply(
                # Latency/Jitter impairment (distribution: constant)
                flow_1.latency_jitter.distribution.constant_delay.set(10000), # 10,000 ns, must be multiples of 100
                flow_1.latency_jitter.schedule.set(1, 0), # continuously increase the latency
                flow_1.latency_jitter.enable.set_on(), # start this impairment

                # Drop impairment (distribution: fixed burst)
                flow_1.drop.distribution.fixed_burst.set(burst_size=5), # drop a fixed burst size 5 frames
                flow_1.drop.schedule.set(1, 5), # drop is on for 10ms and pause for 40ms (total=50ms) (100 drops per second)
                flow_1.drop.enable.set_on(), # start this impairment
            )

            asyncio.create_task(flow_statistic_fetcher(flow_1, stop_event))
            await stop_event.wait()
            await asyncio.sleep(1)


async def main():
    stop_event = asyncio.Event()
    try:
        await impairment_config(stop_event)
    except KeyboardInterrupt:
        stop_event.set()


if __name__ == "__main__":
    asyncio.run(main())