import time
import requests


class WeatherService:
    def __init__(self, config: dict):
        self.config = config
        self._cached_coords = None
        self._cached_at = 0.0

    def _geocode(self, name: str):
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": name, "count": 1, "language": "fi", "format": "json"}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        results = data.get("results") or []
        if not results:
            raise ValueError(f"Paikkaa ei löytynyt: {name}")
        top = results[0]
        return float(top["latitude"]), float(top["longitude"]), top.get("name", name)

    def _get_coords_cached(self):
        if self._cached_coords and (time.time() - self._cached_at) < 24 * 3600:
            return self._cached_coords

        name = self.config.get("location_name", "Helsinki")
        lat, lon, resolved_name = self._geocode(name)
        self._cached_coords = (lat, lon, resolved_name)
        self._cached_at = time.time()
        return self._cached_coords

    def get_weather_summary(self) -> str:
        lat, lon, place = self._get_coords_cached()

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,wind_speed_10m,weather_code",
            "timezone": "Europe/Helsinki",
        }
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        cur = data.get("current") or {}
        temp = cur.get("temperature_2m")
        wind = cur.get("wind_speed_10m")
        code = cur.get("weather_code")

        desc = self._weather_code_to_fi(code)
        return f"{place}: {temp:+.1f}°C, {desc}, tuuli {wind:.1f} m/s"

    @staticmethod
    def _weather_code_to_fi(code) -> str:
        mapping = {
            0: "Selkeää",
            1: "Melkein selkeää",
            2: "Puolipilvistä",
            3: "Pilvistä",
            45: "Sumua",
            48: "Jäätävää sumua",
            61: "Vesisadetta",
            71: "Lumisadetta",
            80: "Sadekuuroja",
            95: "Ukkosta",
        }
        return mapping.get(code, f"Sää (koodi {code})")
