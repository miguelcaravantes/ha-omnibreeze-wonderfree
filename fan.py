"""Fan platform for OmniBreeze Wonderfree."""

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import percentage_to_ranged_value, ranged_value_to_percentage

from .const import (
    DOMAIN,
    DP_MODE,
    DP_OSCILLATION,
    DP_POWER,
    DP_SPEED,
    PRESET_TO_VALUE,
    VALUE_TO_PRESET,
)
from .coordinator import WonderfreeCoordinator
from .entity import WonderfreeEntity

SPEED_RANGE = (1, 5)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([WonderfreeFan(hass.data[DOMAIN][entry.entry_id])])


class WonderfreeFan(WonderfreeEntity, FanEntity):
    _attr_name = "Fan"
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.OSCILLATE
        | FanEntityFeature.PRESET_MODE
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )
    _attr_speed_count = 5
    _attr_preset_modes = list(PRESET_TO_VALUE)

    def __init__(self, coordinator: WonderfreeCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.unique_id}_fan"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.power

    @property
    def percentage(self) -> int:
        if not self.is_on:
            return 0
        return ranged_value_to_percentage(SPEED_RANGE, self.coordinator.data.speed)

    @property
    def oscillating(self) -> bool:
        return self.coordinator.data.oscillating

    @property
    def preset_mode(self) -> str | None:
        return VALUE_TO_PRESET.get(self.coordinator.data.mode)

    async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs) -> None:
        values: list[tuple[int, bool | int]] = [(DP_POWER, True)]
        if percentage:
            values.append(
                (DP_SPEED, round(percentage_to_ranged_value(SPEED_RANGE, percentage)))
            )
        if preset_mode is not None:
            values.append((DP_MODE, PRESET_TO_VALUE[preset_mode]))
        await self.coordinator.async_write(*values)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_write((DP_POWER, False))

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage == 0:
            await self.async_turn_off()
            return
        await self.coordinator.async_write(
            (DP_POWER, True),
            (DP_SPEED, round(percentage_to_ranged_value(SPEED_RANGE, percentage))),
        )

    async def async_oscillate(self, oscillating: bool) -> None:
        await self.coordinator.async_write((DP_OSCILLATION, oscillating))

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        await self.coordinator.async_write((DP_MODE, PRESET_TO_VALUE[preset_mode]))
