"""Base entity for OmniBreeze Wonderfree."""

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_KEY, CONF_PRODUCT_KEY, DOMAIN, MANUFACTURER, MODEL
from .coordinator import WonderfreeCoordinator


class WonderfreeEntity(CoordinatorEntity[WonderfreeCoordinator]):
    _attr_has_entity_name = False

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.data[CONF_DEVICE_KEY])},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=self.coordinator.device_name,
            serial_number=self.coordinator.entry.data[CONF_DEVICE_KEY],
            hw_version=self.coordinator.entry.data[CONF_PRODUCT_KEY],
        )
