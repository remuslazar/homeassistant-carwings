# Nissan Carwings Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Community Forum][forum-shield]][forum]
[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

## Overview

This unofficial integration allows Home Assistant to interact with Nissan Connect vehicles via the legacy Nissan Connect EV (Carwings) API. It serves as an alternative to the discontinued core [nissan_leaf](https://www.home-assistant.io/integrations/nissan_leaf/) integration and draws inspiration from both the core integration and the [NissanConnect](https://github.com/dan-r/HomeAssistant-NissanConnect) integration for newer Nissan models.

## Key Features

- **UI Setup & Configuration**: Easily configure and manage settings directly from the Home Assistant UI.
- **Asynchronous Networking**: Ensures non-blocking calls for a smoother experience.
- **Quick Home Assistant Restarts**: Designed for minimal impact on Home Assistant's restart times.

## Installation

### Using HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.][hacs-repo-badge]][hacs-install]

Or:

1. Open the [HACS](https://hacs.xyz) panel in your Home Assistant frontend.
1. Navigate to the "Integrations" tab.
1. Click the three dots in the top-right corner and select "Custom Repositories."
1. Add a new custom repository:
   - **URL:** `https://github.com/remuslazar/homeassistant-carwings`
   - **Category:** Integration
1. Click "Save" and then click "Install" on the `Nissan Carwings` integration.
### Manually

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `nissan_carwings`.
1. Download _all_ the files from the `custom_components/nissan_carwings/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Nissan Carwings"

## Configuration

Configuration is exclusively done through the Home Assistant UI using your NissanConnectEV credentials. The initial setup will verify your credentials and fetch current data, which may take a moment.

## Adjustable Settings

- **Update Interval**: Frequency of data updates from the API, designed to not wake the car and drain the 12V battery.
- **Polling Interval**: Frequency of status requests to the car, which uses cellular communication and consumes a small amount of battery power from the 12V battery. Recommended setting is every 1-2 hours.
- **Polling Interval While Charging**: Similar to the Polling Interval but for when the car is charging. The default 15-minute interval is generally suitable.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[integration_blueprint]: https://github.com/ludeeus/integration_blueprint
[buymecoffee]: https://www.buymeacoffee.com/remuslazar
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/remuslazar/homeassistant-carwings.svg?style=for-the-badge
[commits]: https://github.com/remuslazar/homeassistant-carwings/commits/main
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/remuslazar/homeassistant-carwings.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Remus%20Lazar%20%40remuslazar-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/remuslazar/homeassistant-carwings.svg?style=for-the-badge
[releases]: https://github.com/remuslazar/homeassistant-carwings/releases
[hacs-repo-badge]: https://my.home-assistant.io/badges/hacs_repository.svg
[hacs-install]: https://my.home-assistant.io/redirect/hacs_repository/?owner=remuslazar&repository=https%3A%2F%2Fgithub.com%2Fremuslazar%2Fhomeassistant-carwings&category=Integration