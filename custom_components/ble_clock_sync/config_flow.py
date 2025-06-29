"""Config flow for the BLE Clock Sync integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.exceptions import HomeAssistantError

if TYPE_CHECKING:
    from homeassistant.components.bluetooth import BluetoothServiceInfo
    from homeassistant.core import HomeAssistant

from .const import (
    CONF_DEVICE_MANUFACTURER,
    CONF_DEVICE_MODEL,
    CONF_TEMP_UNIT,
    CONF_TIME_FORMAT,
    CONF_TIMEOUT,
    CONF_TIMEZONE,
    DEFAULT_TEMP_UNIT,
    DEFAULT_TIME_FORMAT,
    DEFAULT_TIMEOUT,
    DOMAIN,
    SUPPORTED_DEVICES,
    TEMP_UNIT_CELSIUS,
    TEMP_UNIT_FAHRENHEIT,
    TIME_FORMAT_12,
    TIME_FORMAT_24,
)
from .models import ClockSyncAPI, ClockSyncDevice, detect_device_model

_LOGGER = logging.getLogger(__name__)


async def validate_input(
    hass: HomeAssistant,
    discovery_info: BluetoothServiceInfo,
    user_input: dict[str, Any],
) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    device_model = detect_device_model(discovery_info)
    if not device_model:
        raise UnsupportedDeviceError

    device = ClockSyncDevice(
        address=discovery_info.address,
        manufacturer=discovery_info.manufacturer or "",
        model=device_model,
        name=user_input.get(CONF_NAME, discovery_info.name),
        temp_unit=user_input.get(CONF_TEMP_UNIT, DEFAULT_TEMP_UNIT),
        time_format=user_input.get(CONF_TIME_FORMAT, DEFAULT_TIME_FORMAT),
        timeout=user_input.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
    )

    api = ClockSyncAPI(device)
    ble_device = bluetooth.async_ble_device_from_address(
        hass, discovery_info.address, connectable=True
    )

    if not ble_device:
        raise CannotConnectError

    if not await api.test_connection(ble_device):
        raise CannotConnectError

    return {"title": device.name, "device": device}


class BleClockSyncConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BLE Clock Sync."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfo | None = None
        self._device_model: str | None = None

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfo
    ) -> ConfigFlowResult:
        """Handle the bluetooth discovery step."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        device_model = detect_device_model(discovery_info)
        if not device_model:
            return self.async_abort(reason="not_supported")

        self._discovery_info = discovery_info
        self._device_model = device_model

        self.context["title_placeholders"] = {
            "name": discovery_info.name or discovery_info.address
        }

        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if not self._discovery_info:
            return self.async_abort(reason="bluetooth_not_ready")

        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, self._discovery_info, user_input)
            except CannotConnectError:
                errors["base"] = "cannot_connect"
            except UnsupportedDeviceError:
                errors["base"] = "not_supported"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                device: ClockSyncDevice = info["device"]
                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_ADDRESS: device.address,
                        CONF_NAME: device.name,
                        CONF_DEVICE_MANUFACTURER: device.manufacturer,
                        CONF_DEVICE_MODEL: device.model,
                        CONF_TEMP_UNIT: device.temp_unit,
                        CONF_TIME_FORMAT: device.time_format,
                        CONF_TIMEOUT: device.timeout,
                    },
                )

        device_info = SUPPORTED_DEVICES.get(self._device_model or "", {})

        schema_dict: dict[Any, Any] = {
            vol.Optional(
                CONF_NAME,
                default=self._discovery_info.name or self._discovery_info.address,
            ): str,
        }

        if device_info.get("supports_temp_unit", False):
            schema_dict[vol.Optional(CONF_TEMP_UNIT, default=DEFAULT_TEMP_UNIT)] = (
                vol.In([TEMP_UNIT_CELSIUS, TEMP_UNIT_FAHRENHEIT])
            )

        if device_info.get("supports_time_format", False):
            schema_dict[vol.Optional(CONF_TIME_FORMAT, default=DEFAULT_TIME_FORMAT)] = (
                vol.In([TIME_FORMAT_12, TIME_FORMAT_24])
            )

        data_schema = vol.Schema(schema_dict)

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "model": self._device_model or "Unknown",
                "address": self._discovery_info.address,
            },
        )

    async def async_step_options(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle advanced options step."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        device_info = SUPPORTED_DEVICES.get(self._device_model or "", {})

        schema_dict = {}

        if device_info.get("supports_timezone", False):
            schema_dict[vol.Optional(CONF_TIMEZONE)] = vol.Coerce(float)

        schema_dict[vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT)] = vol.All(
            vol.Coerce(int), vol.Range(min=10, max=300)
        )

        options_schema = vol.Schema(schema_dict)

        return self.async_show_form(
            step_id="options",
            data_schema=options_schema,
            description_placeholders={
                "model": self._device_model or "Unknown",
            },
        )


class CannotConnectError(HomeAssistantError):
    """Error to indicate we cannot connect."""


class UnsupportedDeviceError(HomeAssistantError):
    """Error to indicate device is not supported."""
