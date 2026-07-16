"""Sensor platform for OmniBreeze Wonderfree."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import WonderfreeCoordinator
from .entity import WonderfreeEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([WonderfreeTemperature(hass.data[DOMAIN][entry.entry_id])])


class WonderfreeTemperature(WonderfreeEntity, SensorEntity):
    _attr_name = "Room Temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: WonderfreeCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.unique_id}_temperature"

    @property
    def native_value(self) -> int:
        return self.coordinator.data.temperature
