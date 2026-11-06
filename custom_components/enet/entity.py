"""Generic Enet Smart Home Entity Model"""

import asyncio
import logging
from homeassistant.helpers.entity import DeviceInfo, Entity
from custom_components.enet.enet_data.enums import ChannelTypeFunctionName
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# After a command, ask the server for the real state. The state in Home Assistant
# is set before the server confirms, so a command the server did not execute
# would otherwise go unnoticed.
VERIFY_DELAY = 8  # seconds
EVENT_COMMAND_UNCONFIRMED = "enet_command_unconfirmed"


class EnetBaseEntity(Entity):
    """Generic Entity Class for Enet Smart Home entities"""

    _attr_has_entity_name = True

    def _enet_client(self):
        """Return the EnetClient of this entity, None if unknown"""
        return None

    @property
    def available(self):
        """Return False while the Enet server cannot be reached."""
        client = self._enet_client()
        return client is None or client.server_available

    @property
    def should_poll(self):
        """Return the polling state. False means the entity will only update when it has new data."""
        return False

    def _subscribe_availability(self) -> None:
        """Write the state when the server becomes (un)available."""
        client = self._enet_client()
        if client is not None:
            self.async_on_remove(
                client.subscribe_availability(self.async_write_ha_state)
            )


class EnetBaseChannelEntity(EnetBaseEntity, Entity):
    """Generic Entity Class for Enet Smart Home channel"""

    _enet_channel_function = None

    def __init__(self, channel):
        self._name = channel.name
        self.channel = channel

    def _enet_client(self):
        return self.channel.device.client

    @property
    def unique_id(self):
        """Return a unique ID."""
        if self._enet_channel_function:
            return f"{self.channel.uid}-{self._enet_channel_function}"
        return self.channel.uid

    @property
    def name(self):
        """Return the channel name, Home Assistant puts the device name in front.

        A channel named like its device returns None (or only the sensor name),
        so the device name is not shown twice.
        """
        channel_name = self._name
        if channel_name == self.channel.device.name:
            channel_name = None
        sensor_name = getattr(self, "_attr_name", None)
        if channel_name and sensor_name:
            return f"{channel_name} {sensor_name}"
        return channel_name or sensor_name

    @property
    def device_info(self):
        """Link the entity to its device, registered by async_setup_devices"""
        return DeviceInfo(identifiers={(DOMAIN, self.channel.device.uid)})

    @property
    def native_value(self) -> int:
        """Return the last value reported by the sensor."""
        return self.channel.get_current_value(self._enet_channel_function)

    def update_value(self, value: int) -> None:
        """Update the value of the sensor."""
        self.channel.set_current_value(self._enet_channel_function, value)

    async def async_added_to_hass(self) -> None:
        """Subscribe to value updates of the channel when added to hass."""
        self.async_on_remove(self.channel.subscribe(self.on_value_updated))
        self._subscribe_availability()

    async def on_value_updated(self) -> None:
        """Callback function when the value is updated."""
        self.async_write_ha_state()

    def _schedule_verify(self, expected_on: bool) -> None:
        """Check after VERIFY_DELAY seconds that the server executed an on/off command."""
        self._verify_seq = getattr(self, "_verify_seq", 0) + 1
        self.hass.async_create_background_task(
            self._verify(expected_on, self._verify_seq),
            name=f"enet verify {self.entity_id}",
        )

    async def _verify(self, expected_on: bool, seq: int) -> None:
        await asyncio.sleep(VERIFY_DELAY)
        if seq != self._verify_seq:
            return  # a newer command was sent, that one is checked instead
        try:
            actual = await self.channel.get_value(ChannelTypeFunctionName.ON_OFF)
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.warning("Could not verify the state of %s: %s", self.entity_id, err)
            return
        if actual is None or bool(actual) == expected_on:
            return
        _LOGGER.warning(
            "Enet server did not execute turn_%s for %s (server reports %s)",
            "on" if expected_on else "off",
            self.entity_id,
            "on" if actual else "off",
        )
        # Show the real state instead of the assumed one
        self.channel.set_current_value(ChannelTypeFunctionName.ON_OFF, bool(actual))
        self.async_write_ha_state()
        self.hass.bus.async_fire(
            EVENT_COMMAND_UNCONFIRMED,
            {
                "entity_id": self.entity_id,
                "expected": "on" if expected_on else "off",
                "actual": "on" if actual else "off",
            },
        )


class EnetBaseDeviceEntity(EnetBaseEntity, Entity):
    """Generic Entity Class for Enet Smart Home devices"""

    def __init__(self, device):
        self.device = device

    def _enet_client(self):
        return self.device.client

    @property
    def device_info(self):
        """Link the entity to its device, registered by async_setup_devices"""
        return DeviceInfo(identifiers={(DOMAIN, self.device.uid)})
