# sensor.py
"""Sensor platform for Spotová Elektřina."""
import asyncio
import logging
from datetime import datetime, timedelta

import aiohttp

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt

from .const import API_ENDPOINT_HOURLY, API_ENDPOINT_QH, DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = SpotovaElektrinaCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()

    sensors = [SpotovaElektrinaMainSensor(coordinator)]

    # Backward-compatible hourly offsets.
    for i in range(1, 7):
        sensors.append(
            SpotovaElektrinaOffsetSensor(
                coordinator=coordinator,
                offset=timedelta(hours=i),
                unique_id_suffix=f"{i}h",
                name_suffix=f"+{i}h",
            )
        )

    # Quarter-hour offsets for granular visualization.
    for minutes in (15, 30, 45, 60, 75, 90):
        sensors.append(
            SpotovaElektrinaOffsetSensor(
                coordinator=coordinator,
                offset=timedelta(minutes=minutes),
                unique_id_suffix=f"{minutes}m",
                name_suffix=f"+{minutes}m",
            )
        )

    async_add_entities(sensors, True)


class SpotovaElektrinaCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=1),
        )
        self.session = async_get_clientsession(hass)
        self._last_update_slot: tuple[int, int] | None = None

    def _current_slot(self) -> tuple[int, int]:
        """Return current quarter-hour slot as (hour, minute)."""
        now = dt.now()
        return now.hour, (now.minute // 15) * 15

    async def _fetch_json(self, url: str) -> dict:
        """Fetch JSON data from URL."""
        async with asyncio.timeout(10):
            async with self.session.get(url) as response:
                response.raise_for_status()
                data = await response.json()

        if not isinstance(data, dict):
            raise UpdateFailed("Unexpected API response format")

        return data

    async def _async_update_data(self) -> dict:
        """Update data via API."""
        try:
            current_slot = self._current_slot()
            force_update = self._last_update_slot != current_slot
            self._last_update_slot = current_slot

            if not force_update and self.data:
                return self.data

            try:
                return await self._fetch_json(API_ENDPOINT_QH)
            except (asyncio.TimeoutError, aiohttp.ClientError, ValueError) as err:
                _LOGGER.warning(
                    "Quarter-hour endpoint failed (%s), trying hourly fallback",
                    err,
                )
                return await self._fetch_json(API_ENDPOINT_HOURLY)

        except (asyncio.TimeoutError, aiohttp.ClientError, ValueError) as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err


class SpotovaElektrinaBaseSensor(CoordinatorEntity, SensorEntity):
    """Shared logic for Spotová Elektřina sensors."""

    _attr_native_unit_of_measurement = "Kč/kWh"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, DOMAIN)},
            name=DEFAULT_NAME,
            manufacturer="spotovaelektrina.cz",
        )

    def convert_to_kwh(self, price_mwh: float | None) -> float | None:
        """Convert price from MWh to kWh."""
        if price_mwh is None:
            return None
        return round(price_mwh / 1000, 2)

    def _is_qh_data(self, prices: list[dict]) -> bool:
        """Check if prices contain quarter-hour entries."""
        return bool(prices) and "minute" in prices[0]

    def _get_day_prices_for_datetime(
        self, target: datetime, data: dict
    ) -> tuple[list[dict], bool]:
        """Return relevant day price list and whether it's quarter-hour data."""
        now_date = dt.now().date()
        if target.date() == now_date:
            prices = data.get("hoursToday", [])
        elif target.date() == now_date + timedelta(days=1):
            prices = data.get("hoursTomorrow", [])
        else:
            prices = []

        return prices, self._is_qh_data(prices)

    def _get_price_for_datetime(self, target: datetime, data: dict) -> float | None:
        """Get price for target datetime."""
        prices, is_qh = self._get_day_prices_for_datetime(target, data)
        if not prices:
            return None

        if is_qh:
            target_minute = (target.minute // 15) * 15
            price_mwh = next(
                (
                    item.get("priceCZK")
                    for item in prices
                    if item.get("hour") == target.hour
                    and item.get("minute", 0) == target_minute
                ),
                None,
            )
        else:
            price_mwh = next(
                (item.get("priceCZK") for item in prices if item.get("hour") == target.hour),
                None,
            )

        return self.convert_to_kwh(price_mwh)

    def _build_forecast_attributes(self, prices: list[dict]) -> dict[str, float | None]:
        """Build forecast attributes with HH:MM keys."""
        if self._is_qh_data(prices):
            return {
                f"{item.get('hour', 0):02d}:{item.get('minute', 0):02d}": self.convert_to_kwh(
                    item.get("priceCZK")
                )
                for item in prices
            }

        return {
            f"{item.get('hour', 0):02d}:00": self.convert_to_kwh(item.get("priceCZK"))
            for item in prices
        }


class SpotovaElektrinaMainSensor(SpotovaElektrinaBaseSensor):
    """Implementation of the main Spotová Elektřina sensor."""

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

        return self._get_price_for_datetime(dt.now(), self.coordinator.data)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if not self.coordinator.data:
            return {
                "resolution_minutes": None,
                "forecast_today": {},
                "forecast_tomorrow": {},
            }

        today_prices = self.coordinator.data.get("hoursToday", [])
        tomorrow_prices = self.coordinator.data.get("hoursTomorrow", [])

        return {
            "resolution_minutes": 15 if self._is_qh_data(today_prices) else 60,
            "forecast_today": self._build_forecast_attributes(today_prices),
            "forecast_tomorrow": self._build_forecast_attributes(tomorrow_prices),
        }


class SpotovaElektrinaOffsetSensor(SpotovaElektrinaBaseSensor):
    """Implementation of offset Spotová Elektřina sensor."""

    def __init__(
        self,
        coordinator: SpotovaElektrinaCoordinator,
        offset: timedelta,
        unique_id_suffix: str,
        name_suffix: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._offset = offset
        self._attr_unique_id = f"{DOMAIN}_price_{unique_id_suffix}"
        self._attr_name = f"{DEFAULT_NAME} {name_suffix}"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        target_time = dt.now() + self._offset
        return self._get_price_for_datetime(target_time, self.coordinator.data)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        target_time = dt.now() + self._offset
        target_minute = (target_time.minute // 15) * 15

        day_prices, is_qh = self._get_day_prices_for_datetime(
            target_time,
            self.coordinator.data or {},
        )

        return {
            "hour": target_time.strftime("%H:00"),
            "slot": (
                f"{target_time.hour:02d}:{target_minute:02d}"
                if is_qh
                else f"{target_time.hour:02d}:00"
            ),
            "date": target_time.strftime("%Y-%m-%d"),
            "resolution_minutes": 15 if is_qh else 60,
            "data_points_for_day": len(day_prices),
        }
