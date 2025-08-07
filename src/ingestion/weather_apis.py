import requests
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import logging
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeatherAPI:
    """Base class for weather API clients"""
    
    def __init__(self):
        self.config = Config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AirQuality-Platform/1.0'
        })
    
    def make_request(self, url: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """Make HTTP request with retry logic"""
        for attempt in range(self.config.MAX_RETRIES):
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.config.MAX_RETRIES - 1:
                    time.sleep(self.config.RETRY_DELAY)
                else:
                    logger.error(f"All {self.config.MAX_RETRIES} attempts failed for URL: {url}")
                    return None

class OpenWeatherMapAPI(WeatherAPI):
    """OpenWeatherMap API client for weather data"""
    
    def get_current_weather(self, city: str) -> Optional[Dict[str, Any]]:
        """Get current weather data for a city"""
        if not self.config.OPENWEATHER_API_KEY:
            logger.warning("OpenWeatherMap API key not configured")
            return self._generate_simulated_weather(city)
        
        url = f"{self.config.OPENWEATHER_BASE_URL}/weather"
        params = {
            'q': city,
            'appid': self.config.OPENWEATHER_API_KEY,
            'units': 'metric'
        }
        
        data = self.make_request(url, params)
        if not data:
            return self._generate_simulated_weather(city)
        
        return {
            'city': data.get('name'),
            'country': data.get('sys', {}).get('country'),
            'latitude': data.get('coord', {}).get('lat'),
            'longitude': data.get('coord', {}).get('lon'),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'temperature': data.get('main', {}).get('temp'),
            'feels_like': data.get('main', {}).get('feels_like'),
            'humidity': data.get('main', {}).get('humidity'),
            'pressure': data.get('main', {}).get('pressure'),
            'wind_speed': data.get('wind', {}).get('speed'),
            'wind_direction': data.get('wind', {}).get('deg'),
            'clouds': data.get('clouds', {}).get('all'),
            'visibility': data.get('visibility'),
            'description': data.get('weather', [{}])[0].get('description'),
            'weather_main': data.get('weather', [{}])[0].get('main'),
            'source': 'openweathermap'
        }
    
    def get_weather_by_coordinates(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Get current weather data by coordinates"""
        if not self.config.OPENWEATHER_API_KEY:
            logger.warning("OpenWeatherMap API key not configured")
            return None
        
        url = f"{self.config.OPENWEATHER_BASE_URL}/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.config.OPENWEATHER_API_KEY,
            'units': 'metric'
        }
        
        data = self.make_request(url, params)
        if not data:
            return None
        
        return {
            'city': data.get('name'),
            'country': data.get('sys', {}).get('country'),
            'latitude': lat,
            'longitude': lon,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'temperature': data.get('main', {}).get('temp'),
            'feels_like': data.get('main', {}).get('feels_like'),
            'humidity': data.get('main', {}).get('humidity'),
            'pressure': data.get('main', {}).get('pressure'),
            'wind_speed': data.get('wind', {}).get('speed'),
            'wind_direction': data.get('wind', {}).get('deg'),
            'clouds': data.get('clouds', {}).get('all'),
            'visibility': data.get('visibility'),
            'description': data.get('weather', [{}])[0].get('description'),
            'weather_main': data.get('weather', [{}])[0].get('main'),
            'source': 'openweathermap'
        }
    
    def get_air_pollution(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Get air pollution data from OpenWeatherMap"""
        if not self.config.OPENWEATHER_API_KEY:
            return None
        
        url = f"{self.config.OPENWEATHER_BASE_URL}/air_pollution"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.config.OPENWEATHER_API_KEY
        }
        
        data = self.make_request(url, params)
        if not data or 'list' not in data:
            return None
        
        pollution_data = data['list'][0] if data['list'] else {}
        components = pollution_data.get('components', {})
        
        return {
            'latitude': lat,
            'longitude': lon,
            'timestamp': datetime.fromtimestamp(pollution_data.get('dt', 0), timezone.utc).isoformat(),
            'aqi': pollution_data.get('main', {}).get('aqi'),
            'co': components.get('co'),
            'no': components.get('no'),
            'no2': components.get('no2'),
            'o3': components.get('o3'),
            'so2': components.get('so2'),
            'pm25': components.get('pm2_5'),
            'pm10': components.get('pm10'),
            'nh3': components.get('nh3'),
            'source': 'openweathermap_pollution'
        }
    
    def _generate_simulated_weather(self, city: str) -> Dict[str, Any]:
        """Generate simulated weather data"""
        import random
        
        coords = self.config.get_city_coordinates().get(city, {'lat': 0, 'lon': 0})
        
        # Base temperatures by city (rough estimates)
        base_temps = {
            'New York': 15, 'Los Angeles': 20, 'Chicago': 10,
            'London': 12, 'Paris': 14, 'Tokyo': 16,
            'Delhi': 28, 'Beijing': 12
        }
        
        base_temp = base_temps.get(city, 15)
        temperature = random.gauss(base_temp, 10)
        
        return {
            'city': city,
            'country': 'Simulated',
            'latitude': coords['lat'],
            'longitude': coords['lon'],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'temperature': round(temperature, 1),
            'feels_like': round(temperature + random.uniform(-3, 3), 1),
            'humidity': random.randint(30, 90),
            'pressure': random.randint(990, 1030),
            'wind_speed': round(random.uniform(0, 15), 1),
            'wind_direction': random.randint(0, 360),
            'clouds': random.randint(0, 100),
            'visibility': random.randint(5000, 15000),
            'description': random.choice(['clear sky', 'few clouds', 'scattered clouds', 'broken clouds', 'overcast clouds']),
            'weather_main': random.choice(['Clear', 'Clouds', 'Rain', 'Mist']),
            'source': 'simulated'
        }

class WeatherDataCollector:
    """Main class for collecting weather data"""
    
    def __init__(self):
        self.openweather = OpenWeatherMapAPI()
        self.config = Config()
    
    def collect_weather_data(self, city: str) -> Optional[Dict[str, Any]]:
        """Collect weather data for a specific city"""
        logger.info(f"Collecting weather data for {city}")
        
        try:
            weather_data = self.openweather.get_current_weather(city)
            return weather_data
        except Exception as e:
            logger.error(f"Weather data collection failed for {city}: {e}")
            return self.openweather._generate_simulated_weather(city)
    
    def collect_pollution_data(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Collect air pollution data by coordinates"""
        try:
            pollution_data = self.openweather.get_air_pollution(lat, lon)
            return pollution_data
        except Exception as e:
            logger.error(f"Pollution data collection failed for coordinates {lat}, {lon}: {e}")
            return None
    
    def collect_all_cities_weather(self) -> List[Dict[str, Any]]:
        """Collect weather data for all monitored cities"""
        all_weather = []
        
        for city in self.config.MONITORED_CITIES:
            city = city.strip()
            weather_data = self.collect_weather_data(city)
            if weather_data:
                all_weather.append(weather_data)
            
            # Rate limiting
            time.sleep(self.config.REQUEST_DELAY)
        
        logger.info(f"Collected weather data for {len(all_weather)} cities")
        return all_weather
    
    def enrich_air_quality_with_weather(self, air_quality_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich air quality data with weather information"""
        enriched_data = []
        
        for aq_measurement in air_quality_data:
            lat = aq_measurement.get('latitude')
            lon = aq_measurement.get('longitude')
            
            if lat and lon:
                # Get weather data for the same location
                weather_data = self.openweather.get_weather_by_coordinates(lat, lon)
                if weather_data:
                    # Merge weather data with air quality data
                    enriched = {**aq_measurement}
                    enriched.update({
                        'temperature': weather_data.get('temperature'),
                        'humidity': weather_data.get('humidity'),
                        'pressure': weather_data.get('pressure'),
                        'wind_speed': weather_data.get('wind_speed'),
                        'wind_direction': weather_data.get('wind_direction'),
                        'weather_description': weather_data.get('description')
                    })
                    enriched_data.append(enriched)
                else:
                    enriched_data.append(aq_measurement)
            else:
                enriched_data.append(aq_measurement)
            
            # Rate limiting
            time.sleep(0.5)
        
        return enriched_data