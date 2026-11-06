"""Support for Enet scenes"""
import logging
from homeassistant.components.scene import Scene as SceneEntity
from homeassistant.helpers.entity import DeviceInfo

from .aioenet import parse_location_scene
from .const import (
    CONF_LOCATION_SCENES,
    DEFAULT_OPTIONS,
    DOMAIN,
    NAME_ENET_CONTROLLER,
    NAME_ENET_SERVER,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Add Enet scenes"""
    hub = entry.runtime_data

    location_scene_types = entry.options.get(
        CONF_LOCATION_SCENES, DEFAULT_OPTIONS[CONF_LOCATION_SCENES]
    )
    scenes = await hub.get_scenes(location_scene_types)
    async_add_entities(
        [EnetSceneEntity(hub, scene_name, scene_uid) for scene_name, scene_uid in scenes]
    )

    _LOGGER.debug("Finished async setup()")


class EnetSceneEntity(SceneEntity):
    """Representation of a Scene entity.

    Scenes made for Home Assistant ("[libenet...]" in the name) use their own
    name. The location scenes of the server ("~LocSceneLightsOff_Kitchen")
    get a translated name, e.g. "Kitchen all lights off".
    """

    _attr_has_entity_name = True

    def __init__(self, hub, name, uid):
        self.uid = uid
        self.hub = hub
        location_scene = parse_location_scene(name)
        if location_scene is not None:
            scene_type, action, location = location_scene
            self._attr_translation_key = f"location_{scene_type}_{action}"
            self._attr_translation_placeholders = {"location": location}
        else:
            if name.startswith("[libenet") and "]" in name:
                name = name.split("]", 1)[-1].strip()
            self._attr_name = name
        _LOGGER.debug("EnetSceneEntity.init() done %s", name)

    @property
    def unique_id(self):
        """Return the unique id of the scene."""
        return self.uid

    async def async_activate(self, **kwargs):
        """Activate Enet scene."""
        await self.hub.activate_scene(self.uid)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device (service) info."""
        return DeviceInfo(
            identifiers={(DOMAIN, NAME_ENET_CONTROLLER)},
            name=NAME_ENET_SERVER,
        )
