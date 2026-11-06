"""Constants for the Enet Smart Home integration."""

from .enums import ButtonEventType

DOMAIN = "enet"

NAME_ENET_CONTROLLER = "Enet Controller"
NAME_ENET_SERVER = "Enet Smart Home Server"

CONF_SUBTYPE = "subtype"
CONF_UNIQUE_ID = "unique_id"

ATTR_ENET_EVENT = "enet_event"
EVENT_TYPE_INITIAL_PRESS = ButtonEventType.INITIAL_PRESS.value
EVENT_TYPE_SHORT_RELEASE = ButtonEventType.SHORT_RELEASE.value
EVENT_TYPE_LONG_RELEASE = ButtonEventType.LONG_RELEASE.value
EVENT_TYPE_DOUBLE_PRESS = ButtonEventType.DOUBLE_PRESS.value

# Options, changed with the Configure button of the integration
CONF_DOUBLE_PRESS_WINDOW = "double_press_window"
CONF_VERIFY_COMMANDS = "verify_commands"
CONF_VERIFY_DELAY = "verify_delay"
CONF_UNAVAILABLE_AFTER_FAILURES = "unavailable_after_failures"
CONF_REQUEST_TIMEOUT = "request_timeout"
CONF_LOCATION_SCENES = "location_scenes"
CONF_LOG_SERVER_RESPONSES = "log_server_responses"

LOCATION_SCENES_LIGHTS = "lights"
LOCATION_SCENES_BLINDS = "blinds"

DEFAULT_OPTIONS = {
    CONF_DOUBLE_PRESS_WINDOW: 0.5,
    CONF_VERIFY_COMMANDS: True,
    CONF_VERIFY_DELAY: 8,
    CONF_UNAVAILABLE_AFTER_FAILURES: 3,
    CONF_REQUEST_TIMEOUT: 15,
    CONF_LOCATION_SCENES: [LOCATION_SCENES_LIGHTS],
    CONF_LOG_SERVER_RESPONSES: False,
}
