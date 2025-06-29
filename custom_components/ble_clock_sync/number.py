"""Number platform for BLE Clock Sync integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .models import ClockSyncDevice

from .const import CONF_TIMEOUT, DOMAIN

_LOGGER = logging.getLogger(__name__)

NUMBER_TYPES = [
    NumberEntityDescription(
        key="timeout",
        name="Connection timeout",
        icon="mdi:timer-outline",
        mode=NumberMode.BOX,
        native_min_value=10,
        native_max_value=300,
        native_step=1,
        native_unit_of_measurement="s",
        entity_category=EntityCategory.CONFIG,
    ),
]


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BLE Clock Sync number entities from a config entry."""
    device: ClockSyncDevice = entry.runtime_data

    entities = []

    for description in NUMBER_TYPES:
        if description.key == "timezone" and not device.supports_timezone:
            continue
        entities.append(ClockSyncNumber(device, entry, description))

    async_add_entities(entities)


class ClockSyncNumber(NumberEntity):
    """Number entity for BLE Clock Sync configuration."""

    _attr_has_entity_name = True

    def __init__(
        self,
        device: ClockSyncDevice,
        entry: ConfigEntry,
        description: NumberEntityDescription,
    ) -> None:
        """Initialize the number entity."""
        self._device = device
        self._entry = entry
        self.entity_description = description
        self._attr_unique_id = f"{device.address}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.address)},
            name=device.name,
            model=device.model,
            manufacturer="BLE Clock Sync",
            connections={("bluetooth", device.address)},
        )

        if description.key == "timeout":
            self._attr_native_value = device.timeout

    async def async_set_native_value(self, value: float) -> None:
        """Set the native value."""
        if self.entity_description.key == "timeout":
            self._device.timeout = int(value)

            data = dict(self._entry.data)
            data[CONF_TIMEOUT] = int(value)
            self.hass.config_entries.async_update_entry(self._entry, data=data)

        self._attr_native_value = value
