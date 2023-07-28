import asyncio
from loguru import logger
from typing import Dict, Generator, List, TYPE_CHECKING

if TYPE_CHECKING:
    from xoa_driver.v2.ports import PortChimera
    from xoa_driver.internals.hli_v2.ports.port_l23.chimera.port_emulation import (
        StatisticsTotals
    )

from xoa_driver import utils
from xoa_driver.enums import OnOff
from xoa_driver.internals.hli_v2.ports.port_l23.chimera.pe_custom_distribution import (
    CustomDistributions as HLICustomDistributions,
    CustomDistribution as HLICustomDistribution,
)

from chimera_core.core.manager.__dataset import PortConfig, PortConfigLinkFlap, PortConfigPulseError, CustomDistribution
from chimera_core.core.manager.__base import ReserveMixin
from chimera_core.core.manager.flow import FlowManager, FlowManagerContainer


class PortConfigurator:
    def __init__(self, port: "PortChimera") -> None:
        self.port = port

    async def get(self) -> PortConfig:
        """Get port configuration

        :return: Port configuration
        :rtype: PortConfig
        """
        comment, enable_tx, enable_link_flap, link_flap_params, enable_pulse_error, pulse_error_params, \
            emulate, tpld_mode, fcs_error_mode = await asyncio.gather(*(
                self.port.comment.get(),
                self.port.tx_enable.get(),
                self.port.pcs_pma.link_flap.enable.get(),
                self.port.pcs_pma.link_flap.params.get(),
                self.port.pcs_pma.pma_pulse_err_inj.enable.get(),
                self.port.pcs_pma.pma_pulse_err_inj.params.get(),
                self.port.emulate.get(),
                self.port.emulation.tpld_mode.get(),
                self.port.emulation.drop_fcs_errors.get(),
            ))
        link_flap = PortConfigLinkFlap(
            enable=enable_link_flap.on_off,
            duration=link_flap_params.duration,
            period=link_flap_params.period,
            repetition=link_flap_params.repetition,
        )
        pulse_error = PortConfigPulseError(
            enable=enable_pulse_error.on_off,
            duration=pulse_error_params.duration,
            period=pulse_error_params.period,
            repetition=pulse_error_params.repetition,
            coeff=pulse_error_params.coeff,
            exp=pulse_error_params.exp,
        )
        config = PortConfig(
            comment=comment.comment,
            link_flap=link_flap,
            pma_error_pulse=pulse_error,
            enable_tx=enable_tx.on_off,
            enable_impairment=emulate.action,
            tpld_mode=tpld_mode.mode,
            fcs_error_mode=fcs_error_mode.on_off,
        )
        return config

    async def set(self, config: PortConfig) -> None:
        """Set port configuration

        :param config: Port configuration
        :type config: PortConfig
        """
        await utils.apply(
            self.port.comment.set(config.comment),
            self.port.pcs_pma.link_flap.enable.set(config.link_flap.enable),
            self.port.pcs_pma.link_flap.params.set(
                duration=config.link_flap.duration,
                period=config.link_flap.period,
                repetition=config.link_flap.repetition
            ),
            self.port.pcs_pma.pma_pulse_err_inj.enable.set(config.pma_error_pulse.enable),
            self.port.pcs_pma.pma_pulse_err_inj.params.set(
                duration=config.pma_error_pulse.duration,
                period=config.pma_error_pulse.period,
                repetition=config.pma_error_pulse.repetition,
                coeff=config.pma_error_pulse.coeff,
                exp=config.pma_error_pulse.exp,
            ),
            self.port.emulate.set(config.enable_impairment),
            self.port.emulation.tpld_mode.set(config.tpld_mode),
            self.port.emulation.drop_fcs_errors.set(config.fcs_error_mode),
        )

    @property
    def statistics(self) -> "StatisticsTotals":
        """Return the port statistics

        :return: port statistics
        :rtype: StatisticsTotals
        """
        return self.port.emulation.statistics


class CustomDistributionsManager:
    def __init__(self, hli_custom_distributions: HLICustomDistributions) -> None:
        self.hli_custom_distributions = hli_custom_distributions

    async def __read_single_custom_distribution(self, cs: HLICustomDistribution) -> CustomDistribution:
        definition, comment, distribution_type = await utils.apply(
            cs.definition.get(),
            cs.comment.get(),
            cs.type.get(),
        )
        return CustomDistribution(
            custom_distribution_index=cs.custom_distribution_index,
            distribution_type=distribution_type.latency_type,
            linear=definition.linear,
            symmetric=definition.symmetric,
            entry_count=definition.entry_count,
            data_x=definition.data_x,
            comment=comment.comment,
        )

    async def get(self) -> Dict[int, CustomDistribution]:
        await self.hli_custom_distributions.server_sync()
        all_custom_distribution = {
            idx: await self.__read_single_custom_distribution(cd_hli) for idx, cd_hli in self.hli_custom_distributions.items()
        }
        return all_custom_distribution

    async def set_single_distribution(self, index: int, cd: CustomDistribution) -> None:
        await self.hli_custom_distributions.server_sync()
        hli_cd = self.hli_custom_distributions[index]
        await hli_cd.comment.set(cd.comment)
        await hli_cd.definition.set(
            linear=cd.linear,
            symmetric=cd.symmetric,
            entry_count=cd.entry_count,
            data_x=cd.data_x,
        )

    async def add(self, linear: bool, entry_count: int, data_x: List[int], comment: str) -> CustomDistribution:
        cd = await self.hli_custom_distributions.add(
            linear=OnOff(int(linear)),
            entry_count=entry_count,
            data_x=data_x,
            comment=comment,
        )
        cd = await self.__read_single_custom_distribution(cd)
        return cd


class PortManager(ReserveMixin):
    resource_instance: "PortChimera"

    def __init__(self, port: "PortChimera") -> None:
        self.resource_instance = port
        self.config = PortConfigurator(port)
        """Port configurator"""

        self.flows = FlowManagerContainer([FlowManager(f) for f in port.emulation.flow])
        """Port flow manager"""

        self.custom_distributions = CustomDistributionsManager(port.custom_distributions)
        """Port custom distribution manager"""

    async def setup(self) -> "PortManager":
        # await self.port_instance.emulate.set_on()
        return self

    def __await__(self) -> Generator[None, None, "PortManager"]:
        return self.setup().__await__()

    async def reset(self) -> None:
        """Reset the port
        """
        await self.resource_instance.reset.set()