"""Test the BLE Clock Sync integration."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.exceptions import (
    ConfigEntryNotReady,
    HomeAssistantError,
    ServiceValidationError,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

from custom_components.ble_clock_sync import (
    async_setup,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.ble_clock_sync.const import (
    CONF_TIMESTAMP,
    CONF_TIMEZONE,
    DOMAIN,
    SERVICE_SYNC_ALL_CLOCKS_TIME,
    SERVICE_SYNC_CLOCKS_TIME,
)


async def test_async_setup_entry_success(
    hass: HomeAssistant, mock_config_entry_data: dict[str, str]
) -> None:
    """Test successful setup of a config entry."""
    with (
        patch(
            "homeassistant.components.bluetooth.async_ble_device_from_address"
        ) as mock_ble_device,
        patch(
            "custom_components.ble_clock_sync.models.ClockSyncAPI.test_connection"
        ) as mock_test_connection,
    ):
        mock_ble_device.return_value = True
        mock_test_connection.return_value = True

        entry = MagicMock()
        entry.data = mock_config_entry_data
        entry.runtime_data = None

        result = await async_setup_entry(hass, entry)

        assert result is True
        assert entry.runtime_data is not None


async def test_async_setup_entry_device_not_found(
    hass: HomeAssistant,
    mock_config_entry_data: dict[str, str],
) -> None:
    """Test setup when BLE device is not found."""
    with patch(
        "homeassistant.components.bluetooth.async_ble_device_from_address"
    ) as mock_ble_device:
        mock_ble_device.return_value = None

        entry = MagicMock()
        entry.data = mock_config_entry_data

        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, entry)


async def test_async_setup_entry_connection_failed(
    hass: HomeAssistant,
    mock_config_entry_data: dict[str, str],
) -> None:
    """Test setup when connection test fails."""
    with (
        patch(
            "homeassistant.components.bluetooth.async_ble_device_from_address"
        ) as mock_ble_device,
        patch(
            "custom_components.ble_clock_sync.models.ClockSyncAPI.test_connection"
        ) as mock_test_connection,
    ):
        mock_ble_device.return_value = True
        mock_test_connection.return_value = False

        entry = MagicMock()
        entry.data = mock_config_entry_data

        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, entry)


async def test_async_unload_entry(hass: HomeAssistant) -> None:
    """Test unloading a config entry."""
    entry = MagicMock()

    with patch("homeassistant.config_entries.async_unload_platforms") as mock_unload:
        mock_unload.return_value = True

        result = await async_unload_entry(hass, entry)

        assert result is True
        mock_unload.assert_called_once()


async def test_async_setup_service_registration(hass: HomeAssistant) -> None:
    """Test that the sync_time service is registered."""
    result = await async_setup(hass, {})

    assert result is True
    assert hass.services.has_service(DOMAIN, SERVICE_SYNC_ALL_CLOCKS_TIME)
    assert hass.services.has_service(DOMAIN, SERVICE_SYNC_CLOCKS_TIME)


async def test_sync_all_clocks_service(
    hass: HomeAssistant, mock_config_entry_data: dict[str, str]
) -> None:
    """Test sync_time service with configured devices."""
    # Setup the service
    await async_setup(hass, {})

    # Create a mock config entry
    entry = MagicMock()
    entry.data = mock_config_entry_data
    entry.domain = DOMAIN
    entry.state = ConfigEntryState.LOADED
    entry.runtime_data = MagicMock()
    entry.runtime_data.address = "AA:BB:CC:DD:EE:FF"
    entry.runtime_data.name = "Test Clock"

    with (
        patch("homeassistant.config_entries.async_entries") as mock_entries,
        patch(
            "homeassistant.components.bluetooth.async_ble_device_from_address"
        ) as mock_ble_device,
        patch(
            "custom_components.ble_clock_sync.models.ClockSyncAPI.sync_time"
        ) as mock_sync_time,
    ):
        mock_entries.return_value = [entry]
        mock_ble_device.return_value = True
        mock_sync_time.return_value = None

        await hass.services.async_call(
            DOMAIN,
            SERVICE_SYNC_ALL_CLOCKS_TIME,
            {},
            blocking=True,
        )

        mock_sync_time.assert_called_once()


async def test_sync_time_service_no_devices(hass: HomeAssistant) -> None:
    """Test sync_time service with no devices."""
    await async_setup(hass, {})

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SYNC_CLOCKS_TIME,
            {},
            blocking=True,
        )


async def test_sync_time_service_with_devices(
    hass: HomeAssistant, mock_config_entry_data: dict[str, str]
) -> None:
    """Test sync_time service with configured devices."""
    # Setup the service
    await async_setup(hass, {})

    # Create a mock config entry
    entry = MagicMock()
    entry.data = mock_config_entry_data
    entry.domain = DOMAIN
    entry.state = ConfigEntryState.LOADED
    entry.runtime_data = MagicMock()
    entry.runtime_data.address = "AA:BB:CC:DD:EE:FF"
    entry.runtime_data.name = "Test Clock"

    with (
        patch("homeassistant.config_entries.async_entries") as mock_entries,
        patch(
            "homeassistant.components.bluetooth.async_ble_device_from_address"
        ) as mock_ble_device,
        patch(
            "custom_components.ble_clock_sync.models.ClockSyncAPI.sync_time"
        ) as mock_sync_time,
    ):
        mock_entries.return_value = [entry]
        mock_ble_device.return_value = True
        mock_sync_time.return_value = None

        await hass.services.async_call(
            DOMAIN,
            SERVICE_SYNC_CLOCKS_TIME,
            {},
            blocking=True,
        )

        mock_sync_time.assert_called_once()


async def test_sync_time_service_with_specific_device(
    hass: HomeAssistant, mock_config_entry_data: dict[str, str]
) -> None:
    """Test sync_time service with specific device ID."""
    # Setup the service
    await async_setup(hass, {})

    # Create a mock config entry
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = mock_config_entry_data
    entry.domain = DOMAIN
    entry.state = ConfigEntryState.LOADED
    entry.runtime_data = MagicMock()
    entry.runtime_data.address = "AA:BB:CC:DD:EE:FF"
    entry.runtime_data.name = "Test Clock"

    with (
        patch("homeassistant.config_entries.async_get_entry") as mock_get_entry,
        patch(
            "homeassistant.components.bluetooth.async_ble_device_from_address"
        ) as mock_ble_device,
        patch(
            "custom_components.ble_clock_sync.models.ClockSyncAPI.sync_time"
        ) as mock_sync_time,
    ):
        mock_get_entry.return_value = entry
        mock_ble_device.return_value = True
        mock_sync_time.return_value = None

        await hass.services.async_call(
            DOMAIN,
            SERVICE_SYNC_CLOCKS_TIME,
            {"device_id": ["test_entry_id"]},
            blocking=True,
        )

        mock_sync_time.assert_called_once()


async def test_sync_time_service_with_custom_params(
    hass: HomeAssistant, mock_config_entry_data: dict[str, str]
) -> None:
    """Test sync_time service with custom timestamp and timezone."""
    # Setup the service
    await async_setup(hass, {})

    # Create a mock config entry
    entry = MagicMock()
    entry.data = mock_config_entry_data
    entry.domain = DOMAIN
    entry.state = ConfigEntryState.LOADED
    entry.runtime_data = MagicMock()
    entry.runtime_data.address = "AA:BB:CC:DD:EE:FF"
    entry.runtime_data.name = "Test Clock"

    timestamp = 1234567890
    timezone_offset = 2

    with (
        patch("homeassistant.config_entries.async_entries") as mock_entries,
        patch(
            "homeassistant.components.bluetooth.async_ble_device_from_address"
        ) as mock_ble_device,
        patch(
            "custom_components.ble_clock_sync.models.ClockSyncAPI.sync_time"
        ) as mock_sync_time,
    ):
        mock_entries.return_value = [entry]
        mock_ble_device.return_value = True
        mock_sync_time.return_value = None

        await hass.services.async_call(
            DOMAIN,
            SERVICE_SYNC_CLOCKS_TIME,
            {
                CONF_TIMESTAMP: timestamp,
                CONF_TIMEZONE: timezone_offset,
            },
            blocking=True,
        )

        mock_sync_time.assert_called_once_with(
            True,  # noqa: FBT003
            timestamp=timestamp,
            tz_offset=timezone_offset,
        )


async def test_sync_time_service_device_not_found(
    hass: HomeAssistant,
    mock_config_entry_data: dict[str, str],
) -> None:
    """Test sync_time service when BLE device is not found."""
    # Setup the service
    await async_setup(hass, {})

    # Create a mock config entry
    entry = MagicMock()
    entry.data = mock_config_entry_data
    entry.domain = DOMAIN
    entry.state = ConfigEntryState.LOADED
    entry.runtime_data = MagicMock()
    entry.runtime_data.address = "AA:BB:CC:DD:EE:FF"
    entry.runtime_data.name = "Test Clock"

    with (
        patch("homeassistant.config_entries.async_entries") as mock_entries,
        patch(
            "homeassistant.components.bluetooth.async_ble_device_from_address"
        ) as mock_ble_device,
    ):
        mock_entries.return_value = [entry]
        mock_ble_device.return_value = None

        # Service should not raise error, just log warning
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SYNC_CLOCKS_TIME,
            {},
            blocking=True,
        )


async def test_sync_time_service_sync_error(
    hass: HomeAssistant, mock_config_entry_data: dict[str, str]
) -> None:
    """Test sync_time service when sync operation fails."""
    # Setup the service
    await async_setup(hass, {})

    # Create a mock config entry
    entry = MagicMock()
    entry.data = mock_config_entry_data
    entry.domain = DOMAIN
    entry.state = ConfigEntryState.LOADED
    entry.runtime_data = MagicMock()
    entry.runtime_data.address = "AA:BB:CC:DD:EE:FF"
    entry.runtime_data.name = "Test Clock"

    with (
        patch("homeassistant.config_entries.async_entries") as mock_entries,
        patch(
            "homeassistant.components.bluetooth.async_ble_device_from_address"
        ) as mock_ble_device,
        patch(
            "custom_components.ble_clock_sync.models.ClockSyncAPI.sync_time"
        ) as mock_sync_time,
    ):
        mock_entries.return_value = [entry]
        mock_ble_device.return_value = True
        mock_sync_time.side_effect = Exception("Sync failed")

        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_SYNC_CLOCKS_TIME,
                {},
                blocking=True,
            )
