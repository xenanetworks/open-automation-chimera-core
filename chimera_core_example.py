import asyncio
from functools import partial
from typing import List

from loguru import logger

from chimera_core.controller import MainController
from chimera_core.types import distributions, enums, dataset

CHASSIS_IP = "10.20.1.166"
USERNAME = "chimeracore"
MODULE_IDX = 2
PORT_IDX = 0
FLOW_IDX = 1

async def my_awesome_func():

    credentials = dataset.Credentials(
        product=dataset.EProductType.VALKYRIE,
        host=CHASSIS_IP)
    
    controller = await MainController()
    tester_id = await controller.add_tester(credentials=credentials)

    tester = await controller.use(tester_id, username=USERNAME, reserve=False, debug=False)

    port = await tester.use_port(module_id=MODULE_IDX, port_id=PORT_IDX, reserve=True)
    await port.reserve_if_not()
    await port.reset()

    flow = port.flows[FLOW_IDX]
    flow_config = await flow.get()
    flow_config.comment = "On VLAN 111"
    await flow.set(config=flow_config)

    shadow_filter = flow.shadow_filter
    await shadow_filter.clear()
    await shadow_filter.init()

    basic_filter = await shadow_filter.use_basic_mode()
    basic_filter_config = await basic_filter.get()
    ethernet_field = basic_filter_config.layer_2.use_ethernet()
    ethernet_field.src_addr.on(value=dataset.Hex("AAAAAAAAAAAA"), mask=dataset.Hex("FFFFFFFFFFFF"))
    ethernet_field.dest_addr.on(value=dataset.Hex("BBBBBBBBBBBB"), mask=dataset.Hex("FFFFFFFFFFFF"))
    vlan_tag_field = basic_filter_config.layer_2_plus.use_1_vlan_tag()
    vlan_tag_field.include()
    vlan_tag_field.tag_inner.on(value=111, mask=dataset.Hex("0FFF"))
    await basic_filter.set(basic_filter_config)
    await shadow_filter.enable()
    await shadow_filter.apply()

    #----------------------------------------------
    # Impairment - Drop
    # ---------------------------------------------
    #region Impairment - Drop

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
    #region Impairment - Misordering

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
    misordering_config.set_distribution(dist)
    await flow.misordering.start(misordering_config)
    await flow.misordering.stop(misordering_config)

    #endregion

    #----------------------------------------------
    # Impairment - Latency & Jitter
    # ---------------------------------------------
    #region Impairment - Latency & Jitter

    # Fixed Burst distribution for impairment Latency & Jitter
    dist = distributions.latency_jitter.ConstantDelay(delay=1000)


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
    #region Impairment - Duplication

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
    #region Impairment - Corruption

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
    #region Bandwidth Control - Policer

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
    policer_config.apply()
    policer_config.start()
    await flow.policer.start(policer_config)
    await flow.policer.stop(policer_config)

    #endregion

    #----------------------------------------------
    # Bandwidth Control - Shaper
    # ---------------------------------------------
    #region Bandwidth Control - Shaper

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
    shaper_config.apply()
    shaper_config.start()
    await flow.shaper.start(shaper_config)
    await flow.shaper.stop(shaper_config)

    #endregion