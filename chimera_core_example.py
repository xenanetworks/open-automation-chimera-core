import asyncio
from functools import partial
from typing import List
from ipaddress import IPv4Address, IPv6Address
from loguru import logger

from chimera_core.controller import MainController
from chimera_core.types import distributions, enums, dataset

CHASSIS_IP = "10.20.30.42"
USERNAME = "chimeracore"
MODULE_IDX = 2
PORT_IDX = 0
FLOW_IDX = 1

async def my_awesome_func(stop_event: asyncio.Event):

    # create credential object
    credentials = dataset.Credentials(
        product=dataset.EProductType.VALKYRIE,
        host=CHASSIS_IP)
    
    # create chimera core controller object
    controller = await MainController()

    # add chimera emulator into the chassis inventory and get the ID
    tester_id = await controller.add_tester(credentials=credentials)

    # create tester object
    tester = await controller.use(tester_id, username=USERNAME, reserve=False, debug=False)

    # create module object and reserve the module
    module = await tester.use_module(module_id=MODULE_IDX, reserve=True)

    # create port object and reserver the port
    port = await tester.use_port(module_id=MODULE_IDX, port_id=PORT_IDX, reserve=True)

    # free the module in case it is reserved by others
    await module.free(False)

    # reserve the port
    await port.reserve()

    # reset port
    await port.reset()


    #----------------------------------------------
    # Port configuration
    # ---------------------------------------------
    # region Port configuration
    port_config = await port.config.get()
    port_config.comment = "My Chimera Port"

    port_config.set_autoneg_on()
    port_config.set_autoneg_off()

    port_config.set_fcs_error_mode_discard()
    port_config.set_fcs_error_mode_pass()

    port_config.set_link_flap(enable=enums.OnOff.ON, duration=100, period=1000, repetition=0)
    port_config.set_link_flap_off()

    port_config.set_pma_error_pulse(enable=enums.OnOff.ON, duration=100, period=1000, repetition=0, coeff=100, exp=-4)
    port_config.set_pma_error_pulse_off()

    port_config.set_impairment_off()
    port_config.set_impairment_on()

    await port.config.set(port_config)

    # endregion

    #----------------------------------------------
    # Flow configuration + basic filter on a port
    # ---------------------------------------------
    # region Flow configuration + basic filter on a port

    # Configure flow properties
    flow = port.flows[FLOW_IDX]
    flow_config = await flow.get()
    flow_config.comment = "On VLAN 111"
    await flow.set(config=flow_config)

    # Initialize shadow filter on the flow
    shadow_filter = flow.shadow_filter
    await shadow_filter.init()
    await shadow_filter.clear()
    
    # Configure shadow filter to BASIC mode
    basic_filter = await shadow_filter.use_basic_mode()
    basic_filter_config = await basic_filter.get()

    #------------------
    # Ethernet subfilter
    #------------------
    # Use and configure basic-mode shadow filter's Ethernet subfilter
    ethernet_subfilter = basic_filter_config.layer_2.use_ethernet()
    ethernet_subfilter.exclude()
    ethernet_subfilter.include()
    ethernet_subfilter.src_addr.on(value=dataset.Hex("AAAAAAAAAAAA"), mask=dataset.Hex("FFFFFFFFFFFF"))
    ethernet_subfilter.dest_addr.on(value=dataset.Hex("BBBBBBBBBBBB"), mask=dataset.Hex("FFFFFFFFFFFF"))

    #------------------
    # Layer 2+ subfilter
    #------------------
    # Not use basic-mode shadow filter's Layer 2+ subfilter
    layer_2_plus_subfilter = basic_filter_config.layer_2_plus.use_none()

    # Use and configure basic-mode shadow filter's Layer2+ subfilter (One VLAN tag)
    layer_2_plus_subfilter = basic_filter_config.layer_2_plus.use_1_vlan_tag()
    layer_2_plus_subfilter.off()
    layer_2_plus_subfilter.exclude()
    layer_2_plus_subfilter.include()
    layer_2_plus_subfilter.tag_inner.on(value=1234, mask=dataset.Hex("FFF"))
    layer_2_plus_subfilter.pcp_inner.on(value=3, mask=dataset.Hex("7"))

    # Use and configure basic-mode shadow filter's Layer2+ subfilter (Two VLAN tag)
    layer_2_plus_subfilter = basic_filter_config.layer_2_plus.use_2_vlan_tags()
    layer_2_plus_subfilter.off()
    layer_2_plus_subfilter.exclude()
    layer_2_plus_subfilter.include()
    layer_2_plus_subfilter.tag_inner.on(value=1234, mask=dataset.Hex("FFF"))
    layer_2_plus_subfilter.pcp_inner.on(value=3, mask=dataset.Hex("7"))
    layer_2_plus_subfilter.tag_outer.on(value=2345, mask=dataset.Hex("FFF"))
    layer_2_plus_subfilter.pcp_outer.on(value=0, mask=dataset.Hex("7"))

    # Use and configure basic-mode shadow filter's Layer2+ subfilter (MPLS)
    layer_2_plus_subfilter = basic_filter_config.layer_2_plus.use_mpls()
    layer_2_plus_subfilter.off()
    layer_2_plus_subfilter.exclude()
    layer_2_plus_subfilter.include()
    layer_2_plus_subfilter.label.on(value=1000, mask=dataset.Hex("FFFFF"))
    layer_2_plus_subfilter.toc.on(value=0, mask=dataset.Hex("7"))


    #------------------
    # Layer 3 subfilter
    #------------------
    # Not use basic-mode shadow filter's Layer 3 subfilter
    layer_3_subfilter = basic_filter_config.layer_3.use_none()
    
    # Use and configure basic-mode shadow filter's Layer 3 subfilter (IPv4)
    layer_3_subfilter = basic_filter_config.layer_3.use_ipv4()
    layer_3_subfilter.off()
    layer_3_subfilter.exclude()
    layer_3_subfilter.include()
    layer_3_subfilter.src_addr.on(value=IPv4Address("10.0.0.2"), mask=dataset.Hex("FFFFFFFF"))
    layer_3_subfilter.dest_addr.on(value=IPv4Address("11.0.0.2"), mask=dataset.Hex("FFFFFFFF"))
    layer_3_subfilter.dscp.on(value=0, mask=dataset.Hex("FC"))

    # Use and configure basic-mode shadow filter's Layer 3 subfilter (IPv6)
    layer_3_subfilter = basic_filter_config.layer_3.use_ipv6()
    layer_3_subfilter.exclude()
    layer_3_subfilter.include()
    layer_3_subfilter.src_addr.on(value=IPv6Address("2001::2"), mask=dataset.Hex("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"))
    layer_3_subfilter.dest_addr.on(value=IPv6Address("2002::2"), mask=dataset.Hex("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"))


    #------------------
    # Layer 4 subfilter
    #------------------
    # Not use basic-mode shadow filter's Layer 4 subfilter
    layer_4_subfilter = basic_filter_config.layer_4.use_none()
    
    # Use and configure basic-mode shadow filter's Layer 4 subfilter (TCP)
    layer_4_subfilter = basic_filter_config.layer_4.use_tcp()
    layer_4_subfilter.off()
    layer_4_subfilter.exclude()
    layer_4_subfilter.include()
    layer_4_subfilter.src_port.on(value=1234, mask=dataset.Hex("FFFF"))
    layer_4_subfilter.dest_port.on(value=80, mask=dataset.Hex("FFFF"))

    # Use and configure basic-mode shadow filter's Layer 4 subfilter (UDP)
    layer_4_subfilter = basic_filter_config.layer_4.use_udp()
    layer_4_subfilter.off()
    layer_4_subfilter.exclude()
    layer_4_subfilter.include()
    layer_4_subfilter.src_port.on(value=1234, mask=dataset.Hex("FFFF"))
    layer_4_subfilter.dest_port.on(value=80, mask=dataset.Hex("FFFF"))


    #------------------
    # Layer Xena subfilter
    #------------------
    # Not use basic-mode shadow filter's Layer Xena subfilter
    layer_xena_subfilter = basic_filter_config.layer_xena.use_none()

    # Use and configure basic-mode shadow filter's Layer 4 subfilter (TCP)
    layer_xena_subfilter = basic_filter_config.layer_xena.use_tpld()
    layer_xena_subfilter.off()
    layer_xena_subfilter.exclude()
    layer_xena_subfilter.include()
    layer_xena_subfilter.configs


    #------------------
    # Layer Any subfilter
    #------------------
    # Not use basic-mode shadow filter's Layer Any subfilter
    layer_any_subfilter = basic_filter_config.layer_any.use_none()

    # Use and configure basic-mode shadow filter's Layer 4 subfilter (TCP)
    layer_any_subfilter = basic_filter_config.layer_any.use_any_field()
    layer_any_subfilter.off()
    layer_any_subfilter.exclude()
    layer_any_subfilter.include()
    layer_any_subfilter.on(position=0, value=dataset.Hex("112233445566"), mask=dataset.Hex("112233445566"))


    # Enable and apply the basic filter settings
    await basic_filter.set(basic_filter_config)
    await shadow_filter.enable()
    await shadow_filter.apply()

    # endregion

    #----------------------------------------------
    # Flow configuration + extended filter on a port
    # ---------------------------------------------
    # region Flow configuration + extended filter on a port

    # Configure flow properties
    flow = port.flows[FLOW_IDX]
    flow_config = await flow.get()
    flow_config.comment = "On VLAN 111"
    await flow.set(config=flow_config)

    # Initialize shadow filter on the flow
    shadow_filter = flow.shadow_filter
    await shadow_filter.init()
    await shadow_filter.clear()

    # Configure shadow filter to EXTENDED mode
    extended_filter = await shadow_filter.use_extended_mode()
    extended_filter_config = await extended_filter.get()

    # extended_filter_config.protocol_segments =

    
    await extended_filter.set(extended_filter_config)
    await shadow_filter.enable()
    await shadow_filter.apply()

    # endregion

    #----------------------------------------------
    # Impairment - Drop
    # ---------------------------------------------
    # region Impairment - Drop

    # Fixed Burst distribution for impairment Drop
    dist = distributions.drop.FixedBurst(burst_size=5)
    dist.repeat(period=5)
    dist.one_shot()

    # Random Burst distribution for impairment Drop
    dist = distributions.drop.RandomBurst(minimum=1, maximum=10, probability=10_000)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Fixed Rate distribution for impairment Drop
    dist = distributions.drop.FixedRate(probability=10_000)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Bit Error Rate distribution for impairment Drop
    dist = distributions.drop.BitErrorRate(coefficient=1, exponent=1)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Random Rate distribution for impairment Drop
    dist = distributions.drop.RandomRate(probability=10_000)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Gilbert Elliot distribution for impairment Drop
    dist = distributions.drop.GilbertElliot(good_state_impair_prob=0, good_state_trans_prob=0, bad_state_impair_prob=0, bad_state_trans_prob=0)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Uniform distribution for impairment Drop
    dist = distributions.drop.Uniform(minimum=1, maximum=1)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Gaussian distribution for impairment Drop
    dist = distributions.drop.Gaussian(mean=1, sd=1)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Poisson distribution for impairment Drop
    dist = distributions.drop.Poisson(lamda=9)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Gamma distribution for impairment Drop
    dist = distributions.drop.Gamma(shape=1, scale=1)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Custom distribution for impairment Drop
    data_x=[0, 1] * 256
    custom_distribution = await port.custom_distributions.add(
        linear=False,
        entry_count = len(data_x),
        data_x=data_x,
        comment="Example Custom Distribution"
    )
    dist = distributions.drop.Custom(custom_distribution=custom_distribution)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Set distribution and start impairment Drop
    drop_config = await flow.drop.get()
    drop_config.set_distribution(dist)
    await flow.drop.start(drop_config)
    await flow.drop.stop(drop_config)

    #endregion

    #----------------------------------------------
    # Impairment - Misordering
    # ---------------------------------------------
    # region Impairment - Misordering

    # Fixed Burst distribution for impairment Misordering
    dist = distributions.misordering.FixedBurst(burst_size=1)
    dist.repeat(period=5)
    dist.one_shot()

    # Fixed Rate distribution for impairment Misordering
    dist = distributions.misordering.FixedRate(probability=10_000)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Set distribution and start impairment Misordering
    misordering_config = await flow.misordering.get()
    misordering_config.depth = 1
    misordering_config.set_distribution(dist)
    await flow.misordering.start(misordering_config)
    await flow.misordering.stop(misordering_config)

    #endregion

    #----------------------------------------------
    # Impairment - Latency & Jitter
    # ---------------------------------------------
    # region Impairment - Latency & Jitter

    # Fixed Burst distribution for impairment Latency & Jitter
    dist = distributions.latency_jitter.ConstantDelay(delay=100)


    # Random Burst distribution for impairment Latency & Jitter
    dist = distributions.latency_jitter.AccumulateBurst(burst_delay=1300)
    dist.repeat(period=1)
    dist.one_shot()

    # Step distribution for impairment Latency & Jitter
    dist = distributions.latency_jitter.Step(min=1300, max=77000)
    dist.continuous()

    # Uniform distribution for impairment Latency & Jitter
    dist = distributions.latency_jitter.Uniform(minimum=1, maximum=1)
    dist.continuous()

    # Gaussian distribution for impairment Latency & Jitter
    dist = distributions.latency_jitter.Gaussian(mean=1, sd=1)
    dist.continuous()

    # Poisson distribution for impairment Latency & Jitter
    dist = distributions.latency_jitter.Poisson(lamda=9)
    dist.continuous()

    # Gamma distribution for impairment Latency & Jitter
    dist = distributions.latency_jitter.Gamma(shape=1, scale=1)
    dist.continuous()

    # Custom distribution for impairment Latency & Jitter
    data_x=[0, 1] * 256
    custom_distribution = await port.custom_distributions.add(
        linear=False,
        entry_count = len(data_x),
        data_x=data_x,
        comment="Example Custom Distribution"
    )
    dist = distributions.latency_jitter.Custom(custom_distribution=custom_distribution)
    dist.continuous()

    # Set distribution and start impairment Latency & Jitter
    latency_jitter_config = await flow.latency_jitter.get()
    latency_jitter_config.set_distribution(dist)
    await flow.latency_jitter.start(latency_jitter_config)
    await flow.latency_jitter.stop(latency_jitter_config)

    #endregion

    #----------------------------------------------
    # Impairment - Duplication
    # ---------------------------------------------
    # region Impairment - Duplication

    # Fixed Burst distribution for impairment Duplication
    dist = distributions.duplication.FixedBurst(burst_size=5)
    dist.repeat(period=5)
    dist.one_shot()

    # Random Burst distribution for impairment Duplication
    dist = distributions.duplication.RandomBurst(minimum=1, maximum=10, probability=10_000)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Fixed Rate distribution for impairment Duplication
    dist = distributions.duplication.FixedRate(probability=10_000)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Bit Error Rate distribution for impairment Duplication
    dist = distributions.duplication.BitErrorRate(coefficient=1, exponent=1)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Random Rate distribution for impairment Duplication
    dist = distributions.duplication.RandomRate(probability=10_000)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Gilbert Elliot distribution for impairment Duplication
    dist = distributions.duplication.GilbertElliot(good_state_impair_prob=0, good_state_trans_prob=0, bad_state_impair_prob=0, bad_state_trans_prob=0)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Uniform distribution for impairment Duplication
    dist = distributions.duplication.Uniform(minimum=1, maximum=1)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Gaussian distribution for impairment Duplication
    dist = distributions.duplication.Gaussian(mean=1, sd=1)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Poisson distribution for impairment Duplication
    dist = distributions.duplication.Poisson(lamda=9)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Gamma distribution for impairment Duplication
    dist = distributions.duplication.Gamma(shape=1, scale=1)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Custom distribution for impairment Duplication
    data_x=[0, 1] * 256
    custom_distribution = await port.custom_distributions.add(
        linear=False,
        entry_count = len(data_x),
        data_x=data_x,
        comment="Example Custom Distribution"
    )
    dist = distributions.duplication.Custom(custom_distribution=custom_distribution)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Set distribution and start impairment Duplication
    duplication_config = await flow.duplication.get()
    duplication_config.set_distribution(dist)
    await flow.duplication.start(duplication_config)
    await flow.duplication.stop(duplication_config)

    #endregion

    #----------------------------------------------
    # Impairment - Corruption
    # ---------------------------------------------
    # region Impairment - Corruption

    # Fixed Burst distribution for impairment Corruption
    dist = distributions.corruption.FixedBurst(burst_size=5)
    dist.repeat(period=5)
    dist.one_shot()

    # Random Burst distribution for impairment Corruption
    dist = distributions.corruption.RandomBurst(minimum=1, maximum=10, probability=10_000)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Fixed Rate distribution for impairment Corruption
    dist = distributions.corruption.FixedRate(probability=10_000)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Bit Error Rate distribution for impairment Corruption
    dist = distributions.corruption.BitErrorRate(coefficient=1, exponent=1)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Random Rate distribution for impairment Corruption
    dist = distributions.corruption.RandomRate(probability=10_000)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Gilbert Elliot distribution for impairment Corruption
    dist = distributions.corruption.GilbertElliot(good_state_impair_prob=0, good_state_trans_prob=0, bad_state_impair_prob=0, bad_state_trans_prob=0)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Uniform distribution for impairment Corruption
    dist = distributions.corruption.Uniform(minimum=1, maximum=1)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Gaussian distribution for impairment Corruption
    dist = distributions.corruption.Gaussian(mean=1, sd=1)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Poisson distribution for impairment Corruption
    dist = distributions.corruption.Poisson(lamda=9)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Gamma distribution for impairment Corruption
    dist = distributions.corruption.Gamma(shape=1, scale=1)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Custom distribution for impairment Corruption
    data_x=[0, 1] * 256
    custom_distribution = await port.custom_distributions.add(
        linear=False,
        entry_count = len(data_x),
        data_x=data_x,
        comment="Example Custom Distribution"
    )
    dist = distributions.corruption.Custom(custom_distribution=custom_distribution)
    dist.repeat_pattern(duration=1, period=1)
    dist.continuous()

    # Set distribution and start impairment Corruption
    corruption_config = await flow.corruption.get()
    corruption_config.corruption_type = enums.CorruptionType.ETH
    corruption_config.corruption_type = enums.CorruptionType.IP
    corruption_config.corruption_type = enums.CorruptionType.TCP
    corruption_config.corruption_type = enums.CorruptionType.UDP
    corruption_config.set_distribution(dist)
    await flow.corruption.start(corruption_config)
    await flow.corruption.stop(corruption_config)

    #endregion

    #----------------------------------------------
    # Bandwidth Control - Policer
    # ---------------------------------------------
    # region Bandwidth Control - Policer

    # Set and start bandwidth control Policer
    policer_config = await flow.policer.get()
    policer_config.set_control_mode(mode=enums.PolicerMode.L1)
    policer_config.set_control_on_l1()
    policer_config.set_control_mode(mode=enums.PolicerMode.L2)
    policer_config.set_control_on_l2()
    policer_config.mode = enums.PolicerMode.L1
    policer_config.mode = enums.PolicerMode.L2
    policer_config.cir = 10_000
    policer_config.cbs = 1_000
    policer_config.set_on_off(on_off=enums.OnOff.ON)
    policer_config.set_on()
    policer_config.set_on_off(on_off=enums.OnOff.OFF)
    policer_config.set_off()
    await flow.policer.start(policer_config)
    await flow.policer.stop(policer_config)

    #endregion

    #----------------------------------------------
    # Bandwidth Control - Shaper
    # ---------------------------------------------
    # region Bandwidth Control - Shaper

    # Set and start bandwidth control Shaper
    shaper_config = await flow.shaper.get()
    shaper_config.set_control_mode(mode=enums.PolicerMode.L1)
    shaper_config.set_control_on_l1()
    shaper_config.set_control_mode(mode=enums.PolicerMode.L2)
    shaper_config.set_control_on_l2()
    shaper_config.mode = enums.PolicerMode.L1
    shaper_config.mode = enums.PolicerMode.L2
    shaper_config.cir = 10_000
    shaper_config.cbs = 1_000
    shaper_config.buffer_size = 1_000
    shaper_config.set_on_off(on_off=enums.OnOff.ON)
    shaper_config.set_on()
    shaper_config.set_on_off(on_off=enums.OnOff.OFF)
    shaper_config.set_off()
    await flow.shaper.start(shaper_config)
    await flow.shaper.stop(shaper_config)

    #endregion


    #----------------------------------------------
    # Statistics
    # ---------------------------------------------
    # region Statistics

    # flow = await self.__use_flow(self.flow_id)
    # while not self.stop_event.is_set():
    #     rx = await flow.statistics.rx.total.get()
    #     drop = await flow.statistics.total.dropped.get()
    #     logger.debug(f"total received packet: {rx.packet_count}, total dropped: {drop.pkt_drop_count_total}")
    #     await asyncio.sleep(1)

    #endregion

async def main() -> None:
    stop_event = asyncio.Event()
    await my_awesome_func(stop_event=stop_event)


if __name__ == "__main__":
    asyncio.run(main())