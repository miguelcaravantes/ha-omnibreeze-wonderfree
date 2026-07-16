"""Switch platform for OmniBreeze Wonderfree."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, DP_DISPLAY, DP_SOUND
from .coordinator import WonderfreeCoordinator
from .entity import WonderfreeEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        WonderfreeSwitch(
            coordinator, "sound", "Sound", "mdi:volume-high", DP_SOUND
        ),
        WonderfreeSwitch(
            coordinator,
            "display",
            "LED Display",
            "mdi:lightbulb-on-outline",
            DP_DISPLAY,
        ),
    ])


class WonderfreeSwitch(WonderfreeEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: WonderfreeCoordinator,
        key: str,
        name: str,
        icon: str,
        dp: int,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._dp = dp
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{coordinator.entry.unique_id}_{key}"

    @property
    def is_on(self) -> bool:
        return (
            self.coordinator.data.sound
            if self._dp == DP_SOUND
            else self.coordinator.data.display
        )

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_write((self._dp, True))

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_write((self._dp, False))
