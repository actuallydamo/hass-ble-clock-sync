"""Data models for BLE Clock Sync integration."""

from __future__ import annotations

import asyncio
import struct
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from bleak import BleakClient
from bleak.exc import BleakError

if TYPE_CHECKING:
    from homeassistant.components.bluetooth import BluetoothServiceInfo

    from custom_components.ble_clock_sync.types import TempUnit, TimeFormat

from .const import (
    SUPPORTED_DEVICES,
    TEMP_UNIT_CELSIUS,
    TEMP_UNIT_FAHRENHEIT,
    TIME_FORMAT_12,
    TIME_FORMAT_24,
    UUID_TEMP_UNIT,
    UUID_TIME,
)


@dataclass
class ClockSyncDevice:
    """Represents a BLE clock device."""

    address: str
    model: str
    name: str
    manufacturer: str
    temp_unit: TempUnit = TEMP_UNIT_CELSIUS
    time_format: TimeFormat = TIME_FORMAT_24
    timezone_offset: float | None = None
    timeout: int = 60
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    @property
    def supports_time_format(self) -> bool:
        """Return if device supports time format configuration."""
        return SUPPORTED_DEVICES[self.model]["supports_time_format"]

    @property
    def supports_temp_unit(self) -> bool:
        """Return if device supports temperature unit configuration."""
        return SUPPORTED_DEVICES[self.model]["supports_temp_unit"]

    @property
    def supports_timezone(self) -> bool:
        """Return if device supports timezone configuration."""
        return SUPPORTED_DEVICES[self.model]["supports_timezone"]


def detect_device_model(discovery_info: BluetoothServiceInfo) -> str | None:
    """Detect device model from discovery info."""
    device_name = discovery_info.name or ""

    # Prioritize more specific matches
    sorted_models = sorted(SUPPORTED_DEVICES.keys(), key=len, reverse=True)

    for model in sorted_models:
        if model in device_name:
            return model

    return None


def get_localized_timestamp() -> tuple[int, int]:
    """Get current timestamp and timezone offset."""
    now = time.time()
    utc = datetime.fromtimestamp(now, UTC)
    local = datetime.fromtimestamp(now)  # noqa: DTZ006 -- Freezegun won't stub astimezone().tzinfo
    diff = (local.replace(tzinfo=UTC) - utc).total_seconds()
    diff_hours, diff_seconds = divmod(diff, 3600)
    utc_timestamp = int((utc + timedelta(seconds=diff_seconds)).timestamp())
    return utc_timestamp, int(diff_hours)


def parse_timezone_offset(tz_offset: float | str | None) -> tuple[int, int]:
    """Parse timezone offset into hours and seconds components."""
    if tz_offset is not None:
        if isinstance(tz_offset, float) or (
            isinstance(tz_offset, str) and "." in tz_offset
        ):
            offset_hours, offset_partial = divmod(float(tz_offset), 1)
            tz_offset_hours = int(offset_hours)
            tz_offset_seconds = int(offset_partial * 3600)
        else:
            tz_offset_hours = int(tz_offset)
            tz_offset_seconds = 0
    else:
        tz_offset_hours = 0
        tz_offset_seconds = 0
    return tz_offset_hours, tz_offset_seconds


class ClockSyncAPI:
    """API for communicating with BLE clock devices."""

    def __init__(self, device: ClockSyncDevice) -> None:
        """Initialize the API."""
        self.device = device

    async def sync_time(
        self,
        ble_device: Any,
        timestamp: int | None = None,
        tz_offset: float | None = None,
    ) -> None:
        """Sync time to the device."""
        async with self.device.lock:
            if tz_offset is None:
                tz_offset = self.device.timezone_offset
            tz_offset_hours, tz_offset_seconds = parse_timezone_offset(tz_offset)

            if timestamp is None:
                if tz_offset is not None:
                    timestamp = int(time.time()) + tz_offset_seconds
                else:
                    timestamp, tz_offset_hours = get_localized_timestamp()
            elif tz_offset is None:
                _, tz_offset_hours = get_localized_timestamp()

            if tz_offset_seconds:
                timestamp += tz_offset_seconds

            async with BleakClient(ble_device, timeout=self.device.timeout) as client:
                time_data = struct.pack("Ib", timestamp, tz_offset_hours)
                await client.write_gatt_char(UUID_TIME, time_data)

    async def push_configuration(
        self,
        ble_device: Any,
        temp_unit: TempUnit | None = None,
        time_format: TimeFormat | None = None,
    ) -> None:
        """Sync configuration settings to the device without updating time."""
        async with self.device.lock:
            temp_unit = temp_unit or self.device.temp_unit
            time_format = time_format or self.device.time_format

            async with BleakClient(ble_device, timeout=self.device.timeout) as client:
                if self.device.supports_temp_unit and temp_unit in [
                    TEMP_UNIT_CELSIUS,
                    TEMP_UNIT_FAHRENHEIT,
                ]:
                    temp_data = struct.pack(
                        "B", 0x01 if temp_unit == TEMP_UNIT_FAHRENHEIT else 0xFF
                    )
                    await client.write_gatt_char(UUID_TEMP_UNIT, temp_data)

                if self.device.supports_time_format and time_format in [
                    TIME_FORMAT_12,
                    TIME_FORMAT_24,
                ]:
                    clock_data = struct.pack(
                        "IHB", 0, 0, 0xAA if time_format == TIME_FORMAT_12 else 0x00
                    )
                    await client.write_gatt_char(UUID_TIME, clock_data)

    async def sync_all(
        self,
        ble_device: Any,
        timestamp: int | None = None,
        tz_offset: float | None = None,
        temp_unit: TempUnit | None = None,
        time_format: TimeFormat | None = None,
    ) -> None:
        """Sync time and all settings to the device."""
        # Sync time first (including timezone)
        await self.sync_time(ble_device, timestamp, tz_offset)

        # Then sync configuration
        await self.push_configuration(ble_device, temp_unit, time_format)

    async def test_connection(self, ble_device: Any) -> bool:
        """Test if we can connect to the device."""
        async with self.device.lock:
            try:
                async with BleakClient(
                    ble_device, timeout=self.device.timeout
                ) as client:
                    return client.is_connected
            except BleakError:
                return False
