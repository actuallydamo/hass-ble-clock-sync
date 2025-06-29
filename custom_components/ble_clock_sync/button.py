"""Button platform for BLE Clock Sync integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components import bluetooth
from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .models import ClockSyncAPI, ClockSyncDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BLE Clock Sync button from a config entry."""
    device: ClockSyncDevice = entry.runtime_data

    entities = [ClockSyncButton(device, entry)]

    async_add_entities(entities)


class ClockSyncButton(ButtonEntity):
    """Button entity for syncing clock time."""

    _attr_has_entity_name = True
    _attr_name = "Sync time"
    _attr_icon = "mdi:clock-digital"

    def __init__(self, device: ClockSyncDevice, entry: ConfigEntry) -> None:
        """Initialize the button."""
        self._device = device
        self._entry = entry
        self._attr_unique_id = f"{device.address}_sync_time"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.address)},
            name=device.name,
            model=device.model,
            manufacturer=device.manufacturer,
            connections={("bluetooth", device.address)},
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, self._device.address, connectable=True
        )

        if not ble_device:
            _LOGGER.error("Could not find BLE device %s", self._device.address)
            return

        api = ClockSyncAPI(self._device)
        try:
            await api.sync_time(ble_device)
            _LOGGER.info("Successfully synced time on %s", self._device.name)
        except Exception:
            _LOGGER.exception("Failed to sync time on %s", self._device.name)
            raise
