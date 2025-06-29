# BLE Clock Sync

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

A Home Assistant custom integration that allows you to synchronize time and settings on BLE-enabled clock devices.

## Features

- **Time Synchronization**: Sync current time to your BLE clock devices
- **Timezone Support**: Configure timezone offset for accurate local time
- **Temperature Unit Control**: Set temperature display to Celsius or Fahrenheit
- **Time Format Options**: Choose between 12-hour and 24-hour time formats
- **Automatic Discovery**: Automatically discovers supported BLE clock devices
- **Service Integration**: Provides a service for bulk time synchronization

## Supported Devices

Currently supports the following BLE clock devices:

| Device Model | Temperature Unit | Time Format |
|--------------|------------------|-------------|
| LYWSD02 | ✅ | ❌ |
| LYWSD02MMC | ✅ | ✅ |

- Xiaomi BLE Temperature Humidity Clock (LYWSD02)
- Xiaomi BLE Temperature Humidity Clock MMC (LYWSD02MMC)

## Requirements

- Home Assistant 2025.6.3 or later
- Bluetooth adapter / ESPHome Bluetooth proxy
- Compatible BLE clock device within range

## Installation

### HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=actuallydamo&repository=hass-ble-clock-sync&category=integration)

1. Make sure [HACS](https://hacs.xyz/) is installed
2. Add this repository as a custom repository in HACS:
   - Go to HACS --> Integrations
   - Click the three dots menu --> Custom repositories
   - Add repository URL and select "Integration" as category
3. Search for "BLE Clock Sync" in HACS
4. Install the integration
5. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/actuallydamo/hass-ble-clock-sync/releases)
2. Extract the `ble_clock_sync` folder to your `custom_components` directory
3. Restart Home Assistant

## Configuration

Devices should automatically be discovered if supported and within range.

You can click "ADD" under the Discovered section of the Integrations page to add them.

If not, you can manually add them:

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "BLE Clock Sync"
4. Follow the configuration flow:
   - Select your discovered BLE clock device
   - Configure device name
   - Set temperature unit (Celsius/Fahrenheit)
   - Set time format (12/24 hour) if supported
   - Configure timezone offset (optional)
   - Set connection timeout (optional)

### Device Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| Device Name | Friendly name for the device | Device model |
| Temperature Unit | Display unit (C or F) | C |
| Time Format | 12 or 24 hour format | 24 |
| Connection Timeout | Connection timeout in seconds | 60 |

## Usage

### Entities

Each configured device provides the following entities:

#### Button
- **Sync Time**: Manual time synchronization button

#### Select (if supported by device)
- **Temperature Unit**: Change temperature display unit (C/F)
- **Time Format**: Change time format (12/24 hour)

#### Number
- **Connection Timeout**: Adjust connection timeout

### Services

#### `ble_clock_sync.sync_all_clocks_time`

Synchronize time on all supported BLE clock devices.

**Parameters:**
- `timestamp` (optional): UNIX timestamp to set. If empty, uses current time
- `timezone` (optional): Timezone offset in hours (can be decimal, e.g., -5.5)

**Example Service Call:**
```yaml
service: ble_clock_sync.sync_all_clocks_time
data:
  timezone: -5.5
```

**Automation Example:**
```yaml
automation:
  - alias: "Sync all clocks daily"
    trigger:
      platform: time
      at: "02:00:00"
    action:
      service: ble_clock_sync.sync_all_clocks_time
```
#### `ble_clock_sync.sync_clocks_time`

Synchronize time on one or more specific BLE clock devices.

**Parameters:**
- `target`: List of areas, devices, or entities to target
- `timestamp` (optional): UNIX timestamp to set. If empty, uses current time
- `timezone` (optional): Timezone offset in hours (can be decimal, e.g., -5.5)

**Example Service Call:**
```yaml
service: ble_clock_sync.sync_clocks_time
target:
  device_id:
    - "your_device_id"
  area_id:
    - "office"
```

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- @ashald for [home-assistant-lywsd02](https://github.com/ashald/home-assistant-lywsd02) which helped build this.
- @ludeeus for the [integration_blueprint](https://github.com/ludeeus/integration_blueprint) template.

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/actuallydamo/hass-ble-clock-sync.svg?style=for-the-badge
[commits]: https://github.com/actuallydamo/hass-ble-clock-sync/commits/main
[license-shield]: https://img.shields.io/github/license/actuallydamo/hass-ble-clock-sync.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/actuallydamo/hass-ble-clock-sync.svg?style=for-the-badge
[releases]: https://github.com/actuallydamo/hass-ble-clock-sync/releases
