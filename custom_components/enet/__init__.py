"""The Enet Smart Home integration."""

from __future__ import annotations

import logging

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceEntry

from .aioenet import AuthError, EnetClient, EnetServerError, normalize_url
from .const import (
    CONF_DOUBLE_PRESS_WINDOW,
    CONF_LOG_SERVER_RESPONSES,
    CONF_REQUEST_TIMEOUT,
    CONF_UNAVAILABLE_AFTER_FAILURES,
    CONF_VERIFY_COMMANDS,
    CONF_VERIFY_DELAY,
    DEFAULT_OPTIONS,
    DOMAIN,
    NAME_ENET_CONTROLLER,
)
from .device import async_setup_devices
from .events import async_setup_enet_events

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [
    Platform.LIGHT,
    Platform.SCENE,
    Platform.COVER,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
    Platform.EVENT,
]

type EnetConfigEntry = ConfigEntry[EnetClient]


def apply_options(hub: EnetClient, options) -> None:
    """Set the settings of the client from the options of the config entry."""
    options = {**DEFAULT_OPTIONS, **options}
    hub.double_press_window = float(options[CONF_DOUBLE_PRESS_WINDOW])
    hub.verify_commands = bool(options[CONF_VERIFY_COMMANDS])
    hub.verify_delay = int(options[CONF_VERIFY_DELAY])
    hub.unavailable_after_failures = int(options[CONF_UNAVAILABLE_AFTER_FAILURES])
    hub.request_timeout = int(options[CONF_REQUEST_TIMEOUT])
    hub._debug_requests = bool(options[CONF_LOG_SERVER_RESPONSES])


async def async_setup_entry(hass: HomeAssistant, entry: EnetConfigEntry) -> bool:
    """Set up Enet Smart Home from a config entry."""
    _LOGGER.debug("Setting up Enet Smart Home entry")

    hub = EnetClient(
        entry.data["url"],
        entry.data["username"],
        entry.data["password"],
        # noconnect=True,
        # load_file="/workspaces/enet-homeassistant/examples/config_entry-enet-oliver.json",
        # ,noconnect=True, load_file="/workspaces/enet-homeassistant/examples/config_entry-enet-01JRNS5MR3V9DX73M7BQ79KC40.json"
    )
    apply_options(hub, entry.options)

    try:
        await hub.initialize()
    except AuthError as e:
        await hub.close()
        raise ConfigEntryAuthFailed(
            "Invalid username or password for Enet Smart Home"
        ) from e
    except (TimeoutError, aiohttp.ClientError, EnetServerError) as e:
        await hub.close()
        raise ConfigEntryNotReady("Failed to connect to Enet Smart Home") from e
    except Exception:
        # Unexpected errors are logged by Home Assistant, just release the session
        await hub.close()
        raise

    if entry.unique_id is None:
        # Entries of older versions have no unique id, the config flow uses the url
        hass.config_entries.async_update_entry(
            entry, unique_id=normalize_url(entry.data["url"])
        )

    entry.runtime_data = hub
    await async_setup_devices(hass, entry, hub)
    async_setup_enet_events(hass, entry, hub)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload when the options change. Other updates of the entry (unique id,
    # reconfigure, reauth) leave the options alone; those reload themselves.
    applied_options = dict(entry.options)

    async def _async_entry_updated(hass: HomeAssistant, entry: EnetConfigEntry) -> None:
        if dict(entry.options) != applied_options:
            await hass.config_entries.async_reload(entry.entry_id)

    entry.async_on_unload(entry.add_update_listener(_async_entry_updated))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: EnetConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Enet Smart Home entry")
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.close()

    return unload_ok


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: EnetConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Allow manual removal of devices the Enet server no longer reports.

    Devices that still exist on the Enet server (and the controller itself)
    cannot be removed, as they would be recreated on the next reload anyway.
    """
    hub = getattr(config_entry, "runtime_data", None)
    if hub is None:
        return False

    known_uids = {device.uid for device in hub.devices}
    known_uids.add(NAME_ENET_CONTROLLER)

    return not any(
        identifier[0] == DOMAIN and identifier[1] in known_uids
        for identifier in device_entry.identifiers
    )

