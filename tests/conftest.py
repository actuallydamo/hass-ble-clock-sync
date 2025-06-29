"""Fixtures and test setup for BLE Clock Sync tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.bluetooth import BluetoothServiceInfo
from homeassistant.const import CONF_ADDRESS, CONF_NAME

if TYPE_CHECKING:
    from collections.abc import Generator

from custom_components.ble_clock_sync.const import (
    CONF_DEVICE_MANUFACTURER,
    CONF_DEVICE_MODEL,
    CONF_TEMP_UNIT,
    CONF_TIME_FORMAT,
    CONF_TIMEOUT,
    DEFAULT_TEMP_UNIT,
    DEFAULT_TIME_FORMAT,
    DEFAULT_TIMEOUT,
    TEMP_UNIT_CELSIUS,
    TIME_FORMAT_24,
)
from custom_components.ble_clock_sync.models import ClockSyncDevice


@pytest.fixture
def mock_bluetooth_service_info() -> BluetoothServiceInfo:
    """Mock BluetoothServiceInfo for LYWSD02 device."""
    return BluetoothServiceInfo(
        name="LYWSD02",
        address="AA:BB:CC:DD:EE:FF",
        rssi=-60,
        manufacturer_data={},
        service_data={},
        service_uuids=[],
        source="local",
    )


@pytest.fixture
def mock_bluetooth_service_info_mmc() -> BluetoothServiceInfo:
    """Mock BluetoothServiceInfo for LYWSD02MMC device."""
    return BluetoothServiceInfo(
        name="LYWSD02MMC",
        address="AA:BB:CC:DD:EE:FF",
        rssi=-60,
        manufacturer_data={},
        service_data={},
        service_uuids=[],
        source="local",
    )


@pytest.fixture
def mock_unsupported_bluetooth_service_info() -> BluetoothServiceInfo:
    """Mock BluetoothServiceInfo for unsupported device."""
    return BluetoothServiceInfo(
        name="UnsupportedDevice",
        address="AA:BB:CC:DD:EE:FF",
        rssi=-60,
        manufacturer_data={},
        service_data={},
        service_uuids=[],
        source="local",
    )


@pytest.fixture
def mock_device() -> ClockSyncDevice:
    """Mock ClockSyncDevice."""
    return ClockSyncDevice(
        address="AA:BB:CC:DD:EE:FF",
        manufacturer="Xiaomi",
        model="LYWSD02",
        name="Test Clock",
        temp_unit=TEMP_UNIT_CELSIUS,
        time_format=TIME_FORMAT_24,
        timeout=DEFAULT_TIMEOUT,
    )


@pytest.fixture
def mock_device_mmc() -> ClockSyncDevice:
    """Mock ClockSyncDevice for MMC variant."""
    return ClockSyncDevice(
        address="AA:BB:CC:DD:EE:FF",
        manufacturer="Xiaomi",
        model="LYWSD02MMC",
        name="Test Clock MMC",
        temp_unit=TEMP_UNIT_CELSIUS,
        time_format=TIME_FORMAT_24,
        timeout=DEFAULT_TIMEOUT,
    )


@pytest.fixture
def mock_config_entry_data() -> dict[str, Any]:
    """Mock config entry data."""
    return {
        CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
        CONF_NAME: "Test Clock",
        CONF_DEVICE_MANUFACTURER: "Xiaomi",
        CONF_DEVICE_MODEL: "LYWSD02",
        CONF_TEMP_UNIT: DEFAULT_TEMP_UNIT,
        CONF_TIME_FORMAT: DEFAULT_TIME_FORMAT,
        CONF_TIMEOUT: DEFAULT_TIMEOUT,
    }


@pytest.fixture
def mock_ble_device() -> MagicMock:
    """Mock BLE device."""
    mock_device = MagicMock()
    mock_device.address = "AA:BB:CC:DD:EE:FF"
    return mock_device


@pytest.fixture
def mock_bleak_client() -> Generator[AsyncMock]:
    """Mock BleakClient."""
    with patch("custom_components.ble_clock_sync.models.BleakClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.is_connected = True
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_instance
        yield mock_instance
