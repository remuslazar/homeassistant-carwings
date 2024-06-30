# Nissan Carwings Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Community Forum][forum-shield]][forum]

An unofficial integration for interacting with Nissan Connect vehicles using the legacy Nissan Connect EV (Carwings) API.

**This integration will set up the following platforms.**

Platform | Description
-- | --
`binary_sensor` | Show something `True` or `False`.
`sensor` | Show info from blueprint API.
`switch` | Switch something `True` or `False`.

## Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `nissan_carwings`.
1. Download _all_ the files from the `custom_components/nissan_carwings/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Nissan Carwings"

## Configuration is done in the UI

<!---->

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
