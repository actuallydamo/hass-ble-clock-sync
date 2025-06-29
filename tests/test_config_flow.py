"""Test the BLE Clock Sync config flow."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.data_entry_flow import FlowResultType

from custom_components.ble_clock_sync.config_flow import (
    CannotConnectError,
    UnsupportedDeviceError,
    validate_input,
)
from custom_components.ble_clock_sync.const import (
    CONF_TEMP_UNIT,
    CONF_TIME_FORMAT,
    CONF_TIMEOUT,
    DOMAIN,
    TEMP_UNIT_FAHRENHEIT,
    TIME_FORMAT_12,
)

if TYPE_CHECKING:
    from homeassistant.components.bluetooth import BluetoothServiceInfo
    from homeassistant.core import HomeAssistant


async def test_bluetooth_discovery_supported_device(
    hass: HomeAssistant, mock_bluetooth_service_info: BluetoothServiceInfo
) -> None:
    """Test bluetooth discovery of supported device."""
    with patch(
        "homeassistant.components.bluetooth.async_ble_device_from_address"
    ) as mock_ble_device:
        mock_ble_device.return_value = True

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_BLUETOOTH},
            data=mock_bluetooth_service_info,
        )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "bluetooth_confirm"
    assert "name" in result.get("context", {}).get("title_placeholders", {})


async def test_bluetooth_discovery_unsupported_device(
    hass: HomeAssistant,
    mock_unsupported_bluetooth_service_info: BluetoothServiceInfo,
) -> None:
    """Test bluetooth discovery of unsupported device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=mock_unsupported_bluetooth_service_info,
    )

    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "not_supported"


async def test_bluetooth_discovery_already_configured(
    hass: HomeAssistant,
    mock_bluetooth_service_info: BluetoothServiceInfo,
) -> None:
    """Test bluetooth discovery when device is already configured."""
    # Create a mock config entry
    entry = config_entries.ConfigEntry(
        version=1,
        minor_version=1,
        discovery_keys=MappingProxyType({}),
        subentries_data={},
        options={},
        domain=DOMAIN,
        title="Test Clock",
        data={},
        source=config_entries.SOURCE_BLUETOOTH,
        unique_id=mock_bluetooth_service_info.address,
    )
    await hass.config_entries.async_add(entry)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=mock_bluetooth_service_info,
    )

    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "already_configured"


async def test_bluetooth_confirm_success(
    hass: HomeAssistant, mock_bluetooth_service_info: BluetoothServiceInfo
) -> None:
    """Test successful bluetooth confirmation."""
    with (
        patch(
            "homeassistant.components.bluetooth.async_ble_device_from_address"
        ) as mock_ble_device,
        patch(
            "custom_components.ble_clock_sync.config_flow.validate_input"
        ) as mock_validate,
    ):
        mock_ble_device.return_value = True
        mock_validate.return_value = {
            "title": "Test Clock",
            "device": None,
        }

        # Initialize flow with bluetooth discovery
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_BLUETOOTH},
            data=mock_bluetooth_service_info,
        )

        # Confirm the device
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == "Test Clock"


async def test_bluetooth_confirm_cannot_connect(
    hass: HomeAssistant,
    mock_bluetooth_service_info: BluetoothServiceInfo,
) -> None:
    """Test bluetooth confirmation when cannot connect."""
    with (
        patch(
            "homeassistant.components.bluetooth.async_ble_device_from_address"
        ) as mock_ble_device,
        patch(
            "custom_components.ble_clock_sync.config_flow.validate_input"
        ) as mock_validate,
    ):
        mock_ble_device.return_value = True
        mock_validate.side_effect = CannotConnectError

        # Initialize flow with bluetooth discovery
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_BLUETOOTH},
            data=mock_bluetooth_service_info,
        )

        # Confirm the device
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "bluetooth_confirm"
    errors = result.get("errors") or {}
    assert errors.get("base") == "cannot_connect"


async def test_user_step_success(
    hass: HomeAssistant, mock_bluetooth_service_info: BluetoothServiceInfo
) -> None:
    """Test successful user configuration step."""
    with (
        patch(
            "homeassistant.components.bluetooth.async_discovered_service_info"
        ) as mock_discovered,
        patch(
            "homeassistant.components.bluetooth.async_ble_device_from_address"
        ) as mock_ble_device,
        patch(
            "custom_components.ble_clock_sync.config_flow.validate_input"
        ) as mock_validate,
    ):
        mock_discovered.return_value = [mock_bluetooth_service_info]
        mock_ble_device.return_value = True
        mock_validate.return_value = {
            "title": "Test Clock",
            "device": None,
        }

        # Start user flow
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )

        assert result.get("type") is FlowResultType.FORM
        assert result.get("step_id") == "user"

        # Select device
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_ADDRESS: mock_bluetooth_service_info.address},
        )

        assert result.get("type") is FlowResultType.FORM
        assert result.get("step_id") == "user_confirm"

        # Confirm device
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == "Test Clock"


async def test_user_step_no_devices(hass: HomeAssistant) -> None:
    """Test user step when no devices are found."""
    with patch(
        "homeassistant.components.bluetooth.async_discovered_service_info"
    ) as mock_discovered:
        mock_discovered.return_value = []

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )

    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "no_devices_found"


async def test_options_flow(
    hass: HomeAssistant,
    mock_config_entry_data: dict[str, str],
) -> None:
    """Test options flow."""
    # Create a config entry
    entry = config_entries.ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        discovery_keys=MappingProxyType({}),
        subentries_data={},
        title="Test Clock",
        data=mock_config_entry_data,
        source=config_entries.SOURCE_BLUETOOTH,
        unique_id="AA:BB:CC:DD:EE:FF",
        options={},
    )
    await hass.config_entries.async_add(entry)

    # Start options flow
    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "init"

    expected_timeout = 30

    # Configure options
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_TEMP_UNIT: TEMP_UNIT_FAHRENHEIT,
            CONF_TIME_FORMAT: TIME_FORMAT_12,
            CONF_TIMEOUT: expected_timeout,
        },
    )

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    result_data = result.get("data", {})
    assert result_data.get(CONF_TEMP_UNIT) == TEMP_UNIT_FAHRENHEIT
    assert result_data.get(CONF_TIME_FORMAT) == TIME_FORMAT_12
    assert result_data.get(CONF_TIMEOUT) == expected_timeout


async def test_validate_input_supported_device(
    hass: HomeAssistant, mock_bluetooth_service_info: BluetoothServiceInfo
) -> None:
    """Test validate_input with supported device."""
    with patch(
        "homeassistant.components.bluetooth.async_ble_device_from_address"
    ) as mock_ble_device:
        mock_ble_device.return_value = True

        result = await validate_input(
            hass,
            mock_bluetooth_service_info,
            {CONF_NAME: "Custom Name"},
        )

    assert result["title"] == "Custom Name"
    assert result["device"] is not None


async def test_validate_input_unsupported_device(
    hass: HomeAssistant,
    mock_unsupported_bluetooth_service_info: BluetoothServiceInfo,
) -> None:
    """Test validate_input with unsupported device."""
    with pytest.raises(UnsupportedDeviceError):
        await validate_input(
            hass,
            mock_unsupported_bluetooth_service_info,
            {CONF_NAME: "Custom Name"},
        )


async def test_validate_input_no_ble_device(
    hass: HomeAssistant,
    mock_bluetooth_service_info: BluetoothServiceInfo,
) -> None:
    """Test validate_input when BLE device not found."""
    with patch(
        "homeassistant.components.bluetooth.async_ble_device_from_address"
    ) as mock_ble_device:
        mock_ble_device.return_value = None

        with pytest.raises(CannotConnectError):
            await validate_input(
                hass,
                mock_bluetooth_service_info,
                {CONF_NAME: "Custom Name"},
            )


async def test_validate_input_connection_failed(
    hass: HomeAssistant,
    mock_bluetooth_service_info: BluetoothServiceInfo,
) -> None:
    """Test validate_input when connection test fails."""
    with (
        patch(
            "homeassistant.components.bluetooth.async_ble_device_from_address"
        ) as mock_ble_device,
        patch(
            "custom_components.ble_clock_sync.models.ClockSyncAPI.test_connection"
        ) as mock_test,
    ):
        mock_ble_device.return_value = True
        mock_test.return_value = False

        with pytest.raises(CannotConnectError):
            await validate_input(
                hass,
                mock_bluetooth_service_info,
                {CONF_NAME: "Custom Name"},
            )
