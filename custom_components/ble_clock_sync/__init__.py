"""The BLE Clock Sync integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, CONF_NAME, Platform
from homeassistant.exceptions import (
    ConfigEntryNotReady,
    HomeAssistantError,
    ServiceValidationError,
)
from homeassistant.helpers import config_validation as cv

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall
    from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_DEVICE_MANUFACTURER,
    CONF_DEVICE_MODEL,
    CONF_TEMP_UNIT,
    CONF_TIME_FORMAT,
    CONF_TIMEOUT,
    CONF_TIMESTAMP,
    CONF_TIMEZONE,
    DOMAIN,
    SERVICE_SYNC_ALL_CLOCKS_TIME,
    SERVICE_SYNC_CLOCKS_TIME,
)
from .models import ClockSyncAPI, ClockSyncDevice

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BUTTON, Platform.NUMBER, Platform.SELECT]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type BleClockSyncConfigEntry = ConfigEntry[ClockSyncDevice]


async def async_setup_entry(
    hass: HomeAssistant, entry: BleClockSyncConfigEntry
) -> bool:
    """Set up BLE Clock Sync from a config entry."""
    device = ClockSyncDevice(
        address=entry.data[CONF_ADDRESS],
        manufacturer=entry.data[CONF_DEVICE_MANUFACTURER],
        model=entry.data[CONF_DEVICE_MODEL],
        name=entry.data[CONF_NAME],
        temp_unit=entry.data.get(CONF_TEMP_UNIT, "C"),
        time_format=entry.data.get(CONF_TIME_FORMAT, 24),
        timeout=entry.data.get(CONF_TIMEOUT, 60),
    )

    # Test device connection
    ble_device = bluetooth.async_ble_device_from_address(
        hass, device.address, connectable=True
    )
    if not ble_device:
        message = f"BLE device {device.address} not found"
        _LOGGER.error(message)
        raise ConfigEntryNotReady(message)

    api = ClockSyncAPI(device)
    if not await api.test_connection(ble_device):
        message = f"Could not connect to BLE device {device.address}"
        _LOGGER.warning(message)
        raise ConfigEntryNotReady(message)

    entry.runtime_data = device

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: BleClockSyncConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_setup(hass: HomeAssistant, _config: ConfigType) -> bool:
    """Set up the BLE Clock Sync component."""

    async def sync_time_service(call: ServiceCall) -> None:
        """Sync time on specified clock devices."""
        device_addresses = call.data.get("device_id", [])
        timestamp = call.data.get(CONF_TIMESTAMP)
        timezone_offset = call.data.get(CONF_TIMEZONE)

        # If no specific devices specified, use all configured devices
        if not device_addresses:
            entries = [
                entry
                for entry in hass.config_entries.async_entries(DOMAIN)
                if entry.state.recoverable
            ]
        else:
            # Filter to only our supported devices
            entries = []
            for device_id in device_addresses:
                entry = hass.config_entries.async_get_entry(device_id)
                if entry and entry.domain == DOMAIN:
                    entries.append(entry)

        if not entries:
            message = "No compatible clock devices found"
            raise ServiceValidationError(message)

        for entry in entries:
            if not entry.runtime_data:
                continue

            device: ClockSyncDevice = entry.runtime_data
            ble_device = bluetooth.async_ble_device_from_address(
                hass, device.address, connectable=True
            )

            if not ble_device:
                message = f"Could not find BLE device {device.address}"
                _LOGGER.warning(message)
                continue

            api = ClockSyncAPI(device)
            try:
                await api.sync_time(
                    ble_device, timestamp=timestamp, tz_offset=timezone_offset
                )
                _LOGGER.info("Successfully synced time on %s", device.name)
            except Exception as err:
                message = f"Failed to sync time on {device.name}: {err}"
                _LOGGER.exception(message)
                raise HomeAssistantError(message) from err

    hass.services.async_register(DOMAIN, SERVICE_SYNC_CLOCKS_TIME, sync_time_service)
    hass.services.async_register(
        DOMAIN, SERVICE_SYNC_ALL_CLOCKS_TIME, sync_time_service
    )

    return True
