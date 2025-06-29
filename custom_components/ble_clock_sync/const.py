"""Constants for the BLE Clock Sync integration."""

from __future__ import annotations

CONF_DEVICE_MANUFACTURER = "device_manufacturer"
CONF_DEVICE_MODEL = "device_model"
CONF_TEMP_UNIT = "temp_unit"
CONF_TIMEOUT = "timeout"
CONF_TIMESTAMP = "timestamp"
CONF_TIMEZONE = "timezone"
CONF_TIME_FORMAT = "time_format"
DEFAULT_TEMP_UNIT = "C"
DEFAULT_TIMEOUT = 60
DEFAULT_TIME_FORMAT = 24
DOMAIN = "ble_clock_sync"
SERVICE_SYNC_CLOCKS_TIME = "sync_clocks_time"
SERVICE_SYNC_ALL_CLOCKS_TIME = "sync_all_clocks_time"
SUPPORTED_DEVICES = {
    "LYWSD02": {
        "name": "Xiaomi BLE Temperature Humidity Clock",
        "supports_temp_unit": True,
        "supports_time_format": False,
        "supports_timezone": True,
    },
    "LYWSD02MMC": {
        "name": "Xiaomi BLE Temperature Humidity Clock (MMC)",
        "supports_temp_unit": True,
        "supports_time_format": True,
        "supports_timezone": True,
    },
}
TEMP_UNIT_CELSIUS = "C"
TEMP_UNIT_FAHRENHEIT = "F"
TIME_FORMAT_12 = 12
TIME_FORMAT_24 = 24
UUID_TEMP_UNIT = "EBE0CCBE-7A0A-4B0C-8A1A-6FF2997DA3A6"
UUID_TIME = "EBE0CCB7-7A0A-4B0C-8A1A-6FF2997DA3A6"
