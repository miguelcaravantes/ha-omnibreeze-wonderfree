"""OmniBreeze Wonderfree integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import CONF_DEVICE_KEY, DOMAIN, PLATFORMS
from .coordinator import WonderfreeCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = WonderfreeCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    entity_registry = er.async_get(hass)
    obsolete_unique_id = f"{entry.data[CONF_DEVICE_KEY]}_mode"
    sound_unique_id = f"{entry.data[CONF_DEVICE_KEY]}_sound"
    for registry_entry in er.async_entries_for_config_entry(
        entity_registry, entry.entry_id
    ):
        if (
            registry_entry.platform == DOMAIN
            and registry_entry.unique_id == obsolete_unique_id
        ):
            entity_registry.async_remove(registry_entry.entity_id)
        elif (
            registry_entry.platform == DOMAIN
            and registry_entry.unique_id == sound_unique_id
            and registry_entry.original_name == "Button Sound"
        ):
            entity_registry.async_update_entity(
                registry_entry.entity_id, original_name="Sound"
            )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device(
        identifiers={(DOMAIN, entry.data[CONF_DEVICE_KEY])}
    )
    legacy_name = f"{DOMAIN}_{entry.data[CONF_DEVICE_KEY]}"
    if device is not None and device.name_by_user == legacy_name:
        device_registry.async_update_device(device.id, name_by_user=None)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: WonderfreeCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()
    return unload_ok
