"""Sensor platform for Spotová Elektřina."""
import logging
from datetime import datetime, timedelta
import asyncio
import aiohttp
import async_timeout

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    API_ENDPOINT,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = SpotovaElektrinaCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()
    
    sensors = []
    # Senzor pro aktuální hodinu
    sensors.append(SpotovaElektrinaSensor(coordinator, 0, "Aktuální"))
    
    # Senzory pro následující hodiny
    for i in range(1, 7):
        sensors.append(SpotovaElektrinaSensor(coordinator, i, f"+{i}h"))
    
    async_add_entities(sensors, True)

class SpotovaElektrinaCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=30),
        )
        self.session = async_get_clientsession(hass)

    async def _async_update_data(self):
        """Update data via library."""
        try:
            async with async_timeout.timeout(10):
                async with self.session.get(API_ENDPOINT) as response:
                    data = await response.json()
                    return data
        except (asyncio.TimeoutError, aiohttp.ClientError) as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

class SpotovaElektrinaSensor(CoordinatorEntity, SensorEntity):
    """Implementation of the Spotová Elektřina sensor."""

    _attr_native_unit_of_measurement = "CZK/MWh"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: SpotovaElektrinaCoordinator, hour_offset: int, suffix: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.hour_offset = hour_offset
        self._attr_unique_id = f"{DOMAIN}_price_{hour_offset}h"
        self._attr_name = f"{DEFAULT_NAME} {suffix}"

    def get_price_for_hour(self, target_hour: int, data: dict) -> float | None:
        """Get price for specific hour."""
        today_prices = data.get("hoursToday", [])
        tomorrow_prices = data.get("hoursTomorrow", [])
        
        # Nejdřív zkusíme najít v dnešních cenách
        price = next(
            (price["priceCZK"] for price in today_prices if price["hour"] == target_hour),
            None
        )
        
        # Pokud není v dnešních, možná je v zítřejších
        if price is None:
            price = next(
                (price["priceCZK"] for price in tomorrow_prices if price["hour"] == target_hour),
                None
            )
        
        return price

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        current_hour = datetime.now().hour
        target_hour = (current_hour + self.hour_offset) % 24
        
        return self.get_price_for_hour(target_hour, self.coordinator.data)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        current_hour = datetime.now().hour
        target_hour = (current_hour + self.hour_offset) % 24
        
        return {
            "hour": f"{target_hour:02d}:00"
        }