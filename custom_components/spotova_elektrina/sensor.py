"""Sensor platform for Spotová Elektřina."""
import logging
from datetime import datetime
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
    
    async_add_entities([SpotovaElektrinaSensor(coordinator)], True)

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

    def __init__(self, coordinator: SpotovaElektrinaCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_current_price"
        self._attr_name = DEFAULT_NAME

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        current_hour = datetime.now().hour
        today_prices = self.coordinator.data.get("hoursToday", [])
        
        current_price = next(
            (price["priceCZK"] for price in today_prices if price["hour"] == current_hour),
            None,
        )
        
        return current_price

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if not self.coordinator.data:
            return {
                "forecast_today": {},
                "forecast_tomorrow": {}
            }

        today_prices = self.coordinator.data.get("hoursToday", [])
        tomorrow_prices = self.coordinator.data.get("hoursTomorrow", [])

        return {
            "forecast_today": {
                f"{price['hour']:02d}:00": price["priceCZK"]
                for price in today_prices
            },
            "forecast_tomorrow": {
                f"{price['hour']:02d}:00": price["priceCZK"]
                for price in tomorrow_prices
            }
        }