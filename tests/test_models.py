"""Test the BLE Clock Sync models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest
from bleak.exc import BleakError
from freezegun import freeze_time

if TYPE_CHECKING:
    from homeassistant.components.bluetooth import BluetoothServiceInfo

from custom_components.ble_clock_sync.const import (
    TEMP_UNIT_CELSIUS,
    TEMP_UNIT_FAHRENHEIT,
    TIME_FORMAT_12,
    TIME_FORMAT_24,
)
from custom_components.ble_clock_sync.models import (
    ClockSyncAPI,
    ClockSyncDevice,
    detect_device_model,
    get_localized_timestamp,
    parse_timezone_offset,
)


def test_clock_sync_device_properties(mock_device: ClockSyncDevice) -> None:
    """Test ClockSyncDevice properties."""
    # Test LYWSD02 properties
    assert mock_device.supports_temp_unit is True
    assert mock_device.supports_time_format is False
    assert mock_device.supports_timezone is True


def test_clock_sync_device_mmc_properties(mock_device_mmc: ClockSyncDevice) -> None:
    """Test ClockSyncDevice MMC properties."""
    # Test LYWSD02MMC properties
    assert mock_device_mmc.supports_temp_unit is True
    assert mock_device_mmc.supports_time_format is True
    assert mock_device_mmc.supports_timezone is True


def test_detect_device_model_lywsd02(
    mock_bluetooth_service_info: BluetoothServiceInfo,
) -> None:
    """Test device model detection for LYWSD02."""
    model = detect_device_model(mock_bluetooth_service_info)
    assert model == "LYWSD02"


def test_detect_device_model_lywsd02mmc(
    mock_bluetooth_service_info_mmc: BluetoothServiceInfo,
) -> None:
    """Test device model detection for LYWSD02MMC."""
    model = detect_device_model(mock_bluetooth_service_info_mmc)
    assert model == "LYWSD02MMC"


def test_detect_device_model_unsupported(
    mock_unsupported_bluetooth_service_info: BluetoothServiceInfo,
) -> None:
    """Test device model detection for unsupported device."""
    model = detect_device_model(mock_unsupported_bluetooth_service_info)
    assert model is None


def test_get_localized_timestamp() -> None:
    """Test get_localized_timestamp function with frozen time and multiple offsets."""
    # Use a fixed timestamp for consistent testing
    fixed_time = 1609459200  # 2021-01-01 00:00:00 UTC

    # Test various timezone offsets
    for offset, expected_hours, expected_seconds in [
        [-10, -10, 0],
        [-5.5, -6, 1800],
        [-8.75, -9, 900],
        [0, 0, 0],
        [5.5, 5, 1800],
        [8.75, 8, 2700],
        [10, 10, 0],
    ]:
        with freeze_time(datetime.fromtimestamp(fixed_time, UTC), tz_offset=offset):
            timestamp, tz_offset = get_localized_timestamp()

            assert tz_offset == expected_hours, (
                f"Expected hours {expected_hours}, got {tz_offset} for offset {offset}"
            )

            expected_timestamp = fixed_time + expected_seconds
            assert timestamp == expected_timestamp, (
                f"Expected timestamp {expected_timestamp}, got {timestamp} "
                f"for offset {offset}"
            )


def test_parse_timezone_offset_float() -> None:
    """Test parse_timezone_offset with float input."""
    hours, seconds = parse_timezone_offset(2.5)
    assert hours == 2
    assert seconds == 1800  # 0.5 * 3600


def test_parse_timezone_offset_string_with_decimal() -> None:
    """Test parse_timezone_offset with string decimal input."""
    hours, seconds = parse_timezone_offset("1.25")
    assert hours == 1
    assert seconds == 900  # 0.25 * 3600


def test_parse_timezone_offset_int() -> None:
    """Test parse_timezone_offset with integer input."""
    hours, seconds = parse_timezone_offset(3)
    assert hours == 3
    assert seconds == 0


def test_parse_timezone_offset_none() -> None:
    """Test parse_timezone_offset with None input."""
    hours, seconds = parse_timezone_offset(None)
    assert hours == 0
    assert seconds == 0


@pytest.mark.usefixtures("mock_bleak_client")
async def test_clock_sync_api_test_connection_success(
    mock_device: ClockSyncDevice,
    mock_ble_device: AsyncMock,
) -> None:
    """Test successful connection test."""
    api = ClockSyncAPI(mock_device)
    result = await api.test_connection(mock_ble_device)
    assert result is True


async def test_clock_sync_api_test_connection_failure(
    mock_device: ClockSyncDevice,
    mock_ble_device: AsyncMock,
) -> None:
    """Test failed connection test."""
    with patch("custom_components.ble_clock_sync.models.BleakClient") as mock_client:
        mock_client.side_effect = BleakError("Connection failed")

        api = ClockSyncAPI(mock_device)
        result = await api.test_connection(mock_ble_device)
        assert result is False


async def test_clock_sync_api_sync_time_with_timestamp(
    mock_device: ClockSyncDevice,
    mock_ble_device: AsyncMock,
    mock_bleak_client: AsyncMock,
) -> None:
    """Test sync_time with specific timestamp."""
    api = ClockSyncAPI(mock_device)
    timestamp = 1234567890
    tz_offset = 2.5

    await api.sync_time(mock_ble_device, timestamp=timestamp, tz_offset=tz_offset)

    # Verify write_gatt_char was called
    mock_bleak_client.write_gatt_char.assert_called_once()


async def test_clock_sync_api_sync_time_current_time(
    mock_device: ClockSyncDevice,
    mock_ble_device: AsyncMock,
    mock_bleak_client: AsyncMock,
) -> None:
    """Test sync_time with current time."""
    api = ClockSyncAPI(mock_device)

    await api.sync_time(mock_ble_device)

    # Verify write_gatt_char was called
    mock_bleak_client.write_gatt_char.assert_called_once()


async def test_clock_sync_api_push_configuration(
    mock_device_mmc: ClockSyncDevice,
    mock_ble_device: AsyncMock,
    mock_bleak_client: AsyncMock,
) -> None:
    """Test push_configuration."""
    api = ClockSyncAPI(mock_device_mmc)

    await api.push_configuration(
        mock_ble_device,
        temp_unit=TEMP_UNIT_FAHRENHEIT,
        time_format=TIME_FORMAT_12,
    )

    # Verify write_gatt_char was called twice (once for temp unit, once for time format)
    assert mock_bleak_client.write_gatt_char.call_count == 2


async def test_clock_sync_api_push_configuration_no_support(
    mock_device: ClockSyncDevice,
    mock_ble_device: AsyncMock,
    mock_bleak_client: AsyncMock,
) -> None:
    """Test push_configuration with unsupported features."""
    api = ClockSyncAPI(mock_device)

    await api.push_configuration(
        mock_ble_device,
        temp_unit=TEMP_UNIT_FAHRENHEIT,
        time_format=TIME_FORMAT_12,
    )

    # Verify write_gatt_char was called only once (for temp unit)
    assert mock_bleak_client.write_gatt_char.call_count == 1


async def test_clock_sync_api_sync_all(
    mock_device_mmc: ClockSyncDevice,
    mock_ble_device: AsyncMock,
    mock_bleak_client: AsyncMock,
) -> None:
    """Test sync_all method."""
    api = ClockSyncAPI(mock_device_mmc)

    await api.sync_all(
        mock_ble_device,
        timestamp=1234567890,
        tz_offset=2,
        temp_unit=TEMP_UNIT_CELSIUS,
        time_format=TIME_FORMAT_24,
    )

    # Verify write_gatt_char was called (time sync + 2 config writes)
    assert mock_bleak_client.write_gatt_char.call_count == 3
