"""Select platform for BLE Clock Sync integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

from homeassistant.components import bluetooth
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.device_registry import DeviceInfo

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .types import TempUnit, TimeFormat

from .const import (
    CONF_TEMP_UNIT,
    CONF_TIME_FORMAT,
    DOMAIN,
    TEMP_UNIT_CELSIUS,
    TEMP_UNIT_FAHRENHEIT,
    TIME_FORMAT_12,
    TIME_FORMAT_24,
)
from .models import ClockSyncAPI, ClockSyncDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BLE Clock Sync select entities from a config entry."""
    device: ClockSyncDevice = entry.runtime_data

    entities = []

    if device.supports_temp_unit:
        entities.append(TemperatureUnitSelect(device, entry))

    if device.supports_time_format:
        entities.append(TimeFormatSelect(device, entry))

    async_add_entities(entities)


class ClockSyncSelectEntity(SelectEntity):
    """Base class for BLE Clock Sync select entities."""

    _attr_has_entity_name = True

    def __init__(self, device: ClockSyncDevice, entry: ConfigEntry) -> None:
        """Initialize the select entity."""
        self._device = device
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.address)},
            name=device.name,
            model=device.model,
            manufacturer="BLE Clock Sync",
            connections={("bluetooth", device.address)},
        )

    async def _push_configuration(
        self,
        temp_unit: TempUnit | None = None,
        time_format: TimeFormat | None = None,
    ) -> None:
        """Sync setting to device."""
        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, self._device.address, connectable=True
        )

        if not ble_device:
            _LOGGER.error("Could not find BLE device %s", self._device.address)
            return

        api = ClockSyncAPI(self._device)
        try:
            await api.push_configuration(
                ble_device, temp_unit=temp_unit, time_format=time_format
            )
            _LOGGER.info("Successfully updated setting on %s", self._device.name)
        except Exception:
            _LOGGER.exception("Failed to update setting on %s", self._device.name)
            raise


class TemperatureUnitSelect(ClockSyncSelectEntity):
    """Select entity for temperature unit."""

    _attr_name = "Temperature unit"
    _attr_icon = "mdi:temperature-celsius"
    _attr_options: ClassVar[list[str]] = [TEMP_UNIT_CELSIUS, TEMP_UNIT_FAHRENHEIT]

    def __init__(self, device: ClockSyncDevice, entry: ConfigEntry) -> None:
        """Initialize the temperature unit select."""
        super().__init__(device, entry)
        self._attr_unique_id = f"{device.address}_temp_unit"
        self._attr_current_option = device.temp_unit

    async def async_select_option(self, option: str) -> None:
        """Handle the option selection."""
        temp_unit = (
            TEMP_UNIT_FAHRENHEIT
            if option == TEMP_UNIT_FAHRENHEIT
            else TEMP_UNIT_CELSIUS
        )
        await self._push_configuration(temp_unit=temp_unit)
        self._device.temp_unit = temp_unit
        self._attr_current_option = temp_unit

        data = dict(self._entry.data)
        data[CONF_TEMP_UNIT] = option
        self.hass.config_entries.async_update_entry(self._entry, data=data)


class TimeFormatSelect(ClockSyncSelectEntity):
    """Select entity for time format."""

    _attr_name = "Time format"
    _attr_icon = "mdi:clock-outline"
    _attr_options: ClassVar[list[str]] = [str(TIME_FORMAT_12), str(TIME_FORMAT_24)]

    def __init__(self, device: ClockSyncDevice, entry: ConfigEntry) -> None:
        """Initialize the time format select."""
        super().__init__(device, entry)
        self._attr_unique_id = f"{device.address}_time_format"
        self._attr_current_option = str(device.time_format)

    async def async_select_option(self, option: str) -> None:
        """Handle the option selection."""
        time_format = (
            TIME_FORMAT_12 if option == str(TIME_FORMAT_12) else TIME_FORMAT_24
        )
        await self._push_configuration(time_format=time_format)
        self._device.time_format = time_format
        self._attr_current_option = option

        data = dict(self._entry.data)
        data[CONF_TIME_FORMAT] = time_format
        self.hass.config_entries.async_update_entry(self._entry, data=data)
