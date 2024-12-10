# sensor.py
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
from homeassistant.util import dt

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
    # Hlavní senzor se všemi daty
    sensors.append(SpotovaElektrinaMainSensor(coordinator))
    
    # Dodatečné senzory pro jednotlivé hodiny
    for i in range(1, 7):
        sensors.append(SpotovaElektrinaHourSensor(coordinator, i, f"+{i}h"))
    
    async_add_entities(sensors, True)

class SpotovaElektrinaCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),  # Častější kontrola
        )
        self.session = async_get_clientsession(hass)
        self._last_update_hour = None

    async def _async_update_data(self):
        """Update data via library."""
        try:
            current_hour = dt.now().hour
            
            # Vynutit aktualizaci při změně hodiny
            force_update = self._last_update_hour != current_hour
            self._last_update_hour = current_hour

            if force_update or not self.data:
                async with async_timeout.timeout(10):
                    async with self.session.get(API_ENDPOINT) as response:
                        data = await response.json()
                        return data
            return self.data

        except (asyncio.TimeoutError, aiohttp.ClientError) as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

class SpotovaElektrinaMainSensor(CoordinatorEntity, SensorEntity):
    """Implementation of the main Spotová Elektřina sensor."""

    _attr_native_unit_of_measurement = "CZK/kWh"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: SpotovaElektrinaCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_current_price"
        self._attr_name = DEFAULT_NAME

    def convert_to_kwh(self, price_mwh: float | None) -> float | None:
        """Convert price from MWh to kWh."""
        if price_mwh is None:
            return None
        return round(price_mwh / 1000, 2)

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        current_hour = dt.now().hour
        today_prices = self.coordinator.data.get("hoursToday", [])
        
        current_price = next(
            (price["priceCZK"] for price in today_prices if price["hour"] == current_hour),
            None,
        )
        
        return self.convert_to_kwh(current_price)

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
                f"{price['hour']:02d}:00": self.convert_to_kwh(price["priceCZK"])
                for price in today_prices
            },
            "forecast_tomorrow": {
                f"{price['hour']:02d}:00": self.convert_to_kwh(price["priceCZK"])
                for price in tomorrow_prices
            }
        }

class SpotovaElektrinaHourSensor(CoordinatorEntity, SensorEntity):
    """Implementation of the hourly Spotová Elektřina sensor."""

    _attr_native_unit_of_measurement = "CZK/kWh"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: SpotovaElektrinaCoordinator, hour_offset: int, suffix: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.hour_offset = hour_offset
        self._attr_unique_id = f"{DOMAIN}_price_{hour_offset}h"
        self._attr_name = f"{DEFAULT_NAME} {suffix}"

    def convert_to_kwh(self, price_mwh: float | None) -> float | None:
        """Convert price from MWh to kWh."""
        if price_mwh is None:
            return None
        return round(price_mwh / 1000, 2)

    def get_price_for_hour(self, target_hour: int, target_is_tomorrow: bool, data: dict) -> float | None:
        """Get price for specific hour."""
        if target_is_tomorrow:
            prices = data.get("hoursTomorrow", [])
        else:
            prices = data.get("hoursToday", [])
        
        price_mwh = next(
            (price["priceCZK"] for price in prices if price["hour"] == target_hour),
            None
        )
        return self.convert_to_kwh(price_mwh)

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        now = dt.now()
        target_time = now + timedelta(hours=self.hour_offset)
        target_hour = target_time.hour
        target_is_tomorrow = target_time.date() > now.date()
        
        return self.get_price_for_hour(target_hour, target_is_tomorrow, self.coordinator.data)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        now = dt.now()
        target_time = now + timedelta(hours=self.hour_offset)
        
        return {
            "hour": target_time.strftime("%H:00"),
            "date": target_time.strftime("%Y-%m-%d")
        }