"""Test the BLE Clock Sync button platform."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from custom_components.ble_clock_sync.button import ClockSyncButton, async_setup_entry
from custom_components.ble_clock_sync.const import DOMAIN

if TYPE_CHECKING:
    from collections.abc import Iterable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity import Entity

    from custom_components.ble_clock_sync.models import ClockSyncDevice


async def test_async_setup_entry(
    hass: HomeAssistant,
    mock_device: ClockSyncDevice,
) -> None:
    """Test setting up button entities."""
    entry = MagicMock()
    entry.runtime_data = mock_device

    entities = []

    def mock_add_entities(
        new_entities: Iterable[Entity],
        update_before_add: bool = False,  # noqa: ARG001, FBT001, FBT002
    ) -> None:
        entities.extend(new_entities)

    await async_setup_entry(hass, entry, mock_add_entities)

    assert len(entities) == 1
    assert isinstance(entities[0], ClockSyncButton)


def test_clock_sync_button_init(mock_device: ClockSyncDevice) -> None:
    """Test ClockSyncButton initialization."""
    entry = MagicMock()
    button = ClockSyncButton(mock_device, entry)

    assert button.unique_id == f"{mock_device.address}_sync_time"
    assert button.name == "Sync time"
    assert button.icon == "mdi:clock-digital"
    assert button.has_entity_name is True


def test_clock_sync_button_device_info(mock_device: ClockSyncDevice) -> None:
    """Test ClockSyncButton device info."""
    entry = MagicMock()
    button = ClockSyncButton(mock_device, entry)

    device_info = button.device_info
    assert device_info is not None
    assert device_info.get("identifiers") == {(DOMAIN, mock_device.address)}
    assert device_info.get("name") == mock_device.name
    assert device_info.get("model") == mock_device.model
    assert device_info.get("manufacturer") == mock_device.manufacturer
    assert device_info.get("connections") == {("bluetooth", mock_device.address)}


async def test_async_press_success(
    hass: HomeAssistant,
    mock_device: ClockSyncDevice,
) -> None:
    """Test successful button press."""
    entry = MagicMock()
    button = ClockSyncButton(mock_device, entry)
    button.hass = hass

    with (
        patch(
            "homeassistant.components.bluetooth.async_ble_device_from_address"
        ) as mock_ble_device,
        patch(
            "custom_components.ble_clock_sync.models.ClockSyncAPI.sync_time"
        ) as mock_sync_time,
    ):
        mock_ble_device.return_value = True
        mock_sync_time.return_value = None

        await button.async_press()

        mock_sync_time.assert_called_once()


async def test_async_press_device_not_found(
    hass: HomeAssistant,
    mock_device: ClockSyncDevice,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test button press when BLE device is not found."""
    entry = MagicMock()
    button = ClockSyncButton(mock_device, entry)
    button.hass = hass

    with patch(
        "homeassistant.components.bluetooth.async_ble_device_from_address"
    ) as mock_ble_device:
        mock_ble_device.return_value = None

        await button.async_press()

        assert "Could not find BLE device" in caplog.text


async def test_async_press_sync_error(
    hass: HomeAssistant,
    mock_device: ClockSyncDevice,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test button press when sync operation fails."""
    entry = MagicMock()
    button = ClockSyncButton(mock_device, entry)
    button.hass = hass

    with (
        patch(
            "homeassistant.components.bluetooth.async_ble_device_from_address"
        ) as mock_ble_device,
        patch(
            "custom_components.ble_clock_sync.models.ClockSyncAPI.sync_time"
        ) as mock_sync_time,
    ):
        mock_ble_device.return_value = True
        mock_sync_time.side_effect = Exception("Sync failed")

        with pytest.raises(Exception, match="Sync failed"):
            await button.async_press()

        assert "Failed to sync time" in caplog.text
