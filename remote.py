"""Support for Nature Remo TV."""

import logging

from homeassistant.components.remote import RemoteEntity
from homeassistant.core import callback

from . import DOMAIN, NatureRemoBase

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Nature Remo TV."""
    if discovery_info is None:
        return
    _LOGGER.debug("Setting up TV platform.")
    coordinator = hass.data[DOMAIN]["coordinator"]
    api = hass.data[DOMAIN]["api"]
    appliances = coordinator.data["appliances"]

    async_add_entities(
        [
            NatureRemoTV(coordinator, api, appliance)
            for appliance in appliances.values()
            if appliance["type"] == "TV"
        ]
    )


class NatureRemoTV(NatureRemoBase, RemoteEntity):
    """Representation of a Nature Remo TV remote."""

    def __init__(self, coordinator, api, appliance):
        super().__init__(coordinator, appliance)
        self._api = api
        self._appliance_id = appliance["id"]
        self._name = appliance.get("nickname") or appliance["device"]["name"]
        self._buttons = appliance.get("tv", {}).get("buttons", [])
        self._available = True

    @property
    def name(self):
        return self._name

    @property
    def available(self):
        return self._available

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._appliance_id)},
            "name": self._name,
            "manufacturer": self._appliance.get("model", {}).get("manufacturer"),
            "model": self._appliance.get("model", {}).get("name"),
        }

    async def async_send_command(self, command, **kwargs):
        """Send a command to the TV using /1/appliances/{appliance_id}/tv endpoint."""
        if isinstance(command, list):
            command = command[0]

        valid_commands = {btn["name"] for btn in self._buttons if btn.get("name")}
        if command not in valid_commands:
            _LOGGER.error(f"Command '{command}' not valid for TV {self._name}")
            return

        data = {"button": command}
        endpoint = f"/appliances/{self._appliance_id}/tv"
        response = await self._api.post(endpoint, data)

        if response is None:
            _LOGGER.error(f"Failed to send command '{command}' to TV {self._name}")
        else:
            _LOGGER.debug(f"Sent command '{command}' to TV {self._name} successfully")

    @property
    def extra_state_attributes(self):
        """Expose valid commands as attribute."""
        return {
            "commands": sorted(
                [btn["name"] for btn in self._buttons if btn.get("name")]
            )
        }

    @callback
    def _update_callback(self):
        self.async_write_ha_state()
