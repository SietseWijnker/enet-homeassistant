<img src="https://www.enet-smarthome.com/fileadmin/user_upload/Icons/eNet-Logo.svg" width="150" height="150" />

# Enet Smart Home integration for Home Assistant
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

> **This is a fork** of the Enet Smart Home HACS integration by [mnordseth](https://github.com/mnordseth/enet-homeassistant), with the changes listed below. New upstream versions are merged into this fork. Release tags are named after the upstream version they are based on, with a suffix: `2026.11.1-sw.1` is upstream `2026.11.1` with these changes.
>
> For the original integration, issues and the full history, see [mnordseth/enet-homeassistant](https://github.com/mnordseth/enet-homeassistant).

## Changes in this fork

- **Double press of buttons.** Two short presses of the same button within 0.5 seconds fire an extra `double_press` event. It is available on the event entities and as a device trigger ("Button X double pressed"). The single press events are still sent, so an automation on a short press also runs on a double press.
- **Command verification for lights and switches.** Home Assistant shows the new state as soon as a command is sent, before the server confirms it. The Enet server can accept a command without executing it, for example when it hangs. 8 seconds after a turn on or turn off, the real state is read from the server. If it differs, a warning is logged, the entity shows the real state, and the event `enet_command_unconfirmed` is fired with `entity_id`, `expected` and `actual`. Use it in an automation to get a notification.
- **Timeouts for server requests.** A request fails after 15 seconds instead of hanging for up to 5 minutes (the aiohttp default). The event request, which the server holds for up to 30 seconds, has 45 seconds, and reading the device list at startup 60 seconds.
- **Unavailable entities when the server cannot be reached.** After 3 failed event requests in a row, all Enet entities become unavailable. They become available again at the first successful request.
- **States refreshed after an outage.** After a new login (for example when the Enet server restarted) or after the server was unavailable, the current values of all lights, switches and covers are read again. Changes made during the outage would otherwise be missed.
- **Dutch translation** (`translations/nl.json`) of the configuration screens, the battery state and the button triggers.
- **Retry delay capped.** The delay between failed event requests grows by 2 seconds per attempt, up to at most 60 seconds, so the integration picks up a server that is back after a long outage within a minute.

This integration connects a Gira or Jung eNet Smart Home server to Home Assistant. It reads the devices configured on the server and lets you control and monitor them from Home Assistant.

The integration talks to the server on your local network. Changes are pushed by the server as they happen, so there is no polling.

## Supported features

| Enet channel | Home Assistant entity |
|---|---|
| Switching and dimming light actuators | Light (on/off, brightness for dimmers) |
| Switching actuators | Switch |
| Blind, shutter and awning actuators | Cover (open, close, stop, position; tilt for blinds) |
| Energy sensors | Sensors for power, current, voltage and total energy |
| Light sensors | Illuminance sensor |
| Motion detectors | Motion binary sensor |
| Buttons, rockers and scene buttons | Event entities and device triggers (see below) |
| Battery powered devices | Battery state sensor (diagnostic) |
| Scenes on the Enet server | Scene (see below) |

### Buttons

Every button creates an event entity, and a rocker creates one for each side. Each button can be used as a device trigger in automations for:

- Initial press
- Release after a short press
- Release after a long press
- Double press (this fork)

Button presses are also fired on the event bus as `enet_event`, with the data `device_id`, `unique_id`, `type` (`initial_press`, `short_release`, `long_release` or `double_press`) and `subtype` (the button number).

### Scenes

Scenes defined in the Enet app can be activated from Home Assistant.

### Motion detectors

The motion sensor turns on when the detector reports motion, and turns off after the time reported by the detector. On startup it is off until the first motion is reported.

## Requirements

- Home Assistant 2024.11 or newer
- A Gira or Jung eNet Smart Home server reachable from Home Assistant
- A user account on the Enet server

## Installation using HACS

1. Add `https://github.com/SietseWijnker/enet-homeassistant` as a custom repository inside HACS settings. Make sure you select `Integration` as Category.
2. Search for enet in the Overview page and install the component.
3. Restart Home Assistant.

To switch from the upstream integration, both use the same folder `custom_components/enet`:

1. Remove the upstream repository in HACS. This deletes the files, but do not restart Home Assistant yet; it keeps running with the loaded integration.
2. Add this fork as a custom repository and download it.
3. Restart Home Assistant.

Removing the upstream repository after downloading the fork would delete the files of the fork. The configuration, devices and entities are kept, because they belong to the `enet` domain and not to the repository.

## Configuration

1. Go to **Settings → Devices & services → Add integration** and search for **Enet Smart Home**.
2. Enter:
   - **URL**: the address of the Enet server, for example `http://192.168.1.10`. Use `https://` if the server is set up for it. The server's certificate is not verified.
   - **Username** and **Password** of a user on the Enet server.

The login is checked before the integration is added. Each Enet server can only be added once.

To change the URL or the login later, open the integration and select **Reconfigure**. If the server rejects the login, Home Assistant asks for the username and password again.

Setting up a server found by network discovery is not supported yet. Add the integration manually as described above.

## Removal

1. Go to **Settings → Devices & services**, select **Enet Smart Home**, open the menu (⋮) of the entry and select **Delete**. This removes all devices and entities of the integration from Home Assistant. Nothing is changed on the Enet server.
2. To remove the files as well, open HACS, find **enet**, select **Remove** and restart Home Assistant.

A device that has been removed from the Enet server stays in Home Assistant until you delete it from its device page.

## Troubleshooting

- **Diagnostics**: on the integration page, open the menu (⋮) and select **Download diagnostics**. The file contains the data read from the Enet server. The username and password are removed.
- **Debug logging**: add this to `configuration.yaml` and restart Home Assistant:

  ```yaml
  logger:
    logs:
      custom_components.enet: debug
  ```
