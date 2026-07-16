"""Select entities for OmniBreeze Wonderfree."""

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, DP_COUNTDOWN
from .coordinator import WonderfreeCoordinator
from .entity import WonderfreeEntity

COUNTDOWN_OPTIONS = ["off", *[f"{hour}_hour" for hour in range(1, 13)]]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([WonderfreeCountdown(hass.data[DOMAIN][entry.entry_id])])


class WonderfreeCountdown(WonderfreeEntity, SelectEntity):
    _attr_name = "Auto-off Timer"
    _attr_options = COUNTDOWN_OPTIONS

    def __init__(self, coordinator: WonderfreeCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.unique_id}_countdown"

    @property
    def current_option(self) -> str | None:
        value = self.coordinator.data.countdown
        return (
            COUNTDOWN_OPTIONS[value]
            if 0 <= value < len(COUNTDOWN_OPTIONS)
            else None
        )

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_write(
            (DP_COUNTDOWN, COUNTDOWN_OPTIONS.index(option))
        )
