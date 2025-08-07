import requests
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import logging
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AirQualityAPI:
    """Base class for air quality API clients"""
    
    def __init__(self):
        self.config = Config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AirQuality-Platform/1.0'
        })
    
    def make_request(self, url: str, params: Dict[str, Any] = None, max_retries: int = 3) -> Optional[Dict]:
        """Make HTTP request with retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(self.config.RETRY_DELAY)
                else:
                    logger.error(f"All {max_retries} attempts failed for URL: {url}")
                    return None
    
    def calculate_aqi(self, pollutant: str, value: float) -> tuple[int, str]:
        """Calculate AQI based on pollutant concentration"""
        # US EPA AQI breakpoints
        if pollutant.lower() == 'pm2.5':
            breakpoints = [
                (0, 12.0, 0, 50),
                (12.1, 35.4, 51, 100),
                (35.5, 55.4, 101, 150),
                (55.5, 150.4, 151, 200),
                (150.5, 250.4, 201, 300),
                (250.5, 500.4, 301, 500)
            ]
        elif pollutant.lower() == 'pm10':
            breakpoints = [
                (0, 54, 0, 50),
                (55, 154, 51, 100),
                (155, 254, 101, 150),
                (255, 354, 151, 200),
                (355, 424, 201, 300),
                (425, 604, 301, 500)
            ]
        elif pollutant.lower() == 'o3':
            breakpoints = [
                (0, 54, 0, 50),
                (55, 70, 51, 100),
                (71, 85, 101, 150),
                (86, 105, 151, 200),
                (106, 200, 201, 300)
            ]
        else:
            return 50, "Moderate"  # Default
        
        for low, high, aqi_low, aqi_high in breakpoints:
            if low <= value <= high:
                aqi = ((aqi_high - aqi_low) / (high - low)) * (value - low) + aqi_low
                category = self.get_aqi_category(int(aqi))
                return int(aqi), category
        
        return 500, "Hazardous"  # If value exceeds all breakpoints
    
    def get_aqi_category(self, aqi: int) -> str:
        """Get AQI category based on value"""
        if aqi <= 50:
            return "Good"
        elif aqi <= 100:
            return "Moderate"
        elif aqi <= 150:
            return "Unhealthy for Sensitive Groups"
        elif aqi <= 200:
            return "Unhealthy"
        elif aqi <= 300:
            return "Very Unhealthy"
        else:
            return "Hazardous"

class OpenAQAPI(AirQualityAPI):
    """OpenAQ API client for air quality data"""
    
    def get_latest_measurements(self, city: str, country: str = None) -> List[Dict[str, Any]]:
        """Get latest air quality measurements for a city"""
        url = f"{self.config.OPENAQ_BASE_URL}/latest"
        params = {
            'city': city,
            'limit': 100
        }
        if country:
            params['country'] = country
        
        data = self.make_request(url, params)
        if not data or 'results' not in data:
            return []
        
        measurements = []
        for result in data['results']:
            for measurement in result.get('measurements', []):
                processed_data = {
                    'city': result.get('city'),
                    'country': result.get('country'),
                    'latitude': result['coordinates'].get('latitude') if result.get('coordinates') else None,
                    'longitude': result['coordinates'].get('longitude') if result.get('coordinates') else None,
                    'timestamp': measurement.get('lastUpdated'),
                    'parameter': measurement.get('parameter'),
                    'value': measurement.get('value'),
                    'unit': measurement.get('unit'),
                    'source': 'openaq'
                }
                measurements.append(processed_data)
        
        return measurements

class IQAirAPI(AirQualityAPI):
    """IQAir API client for air quality data"""
    
    def get_city_data(self, city: str, country: str = None) -> Optional[Dict[str, Any]]:
        """Get air quality data for a city"""
        if not self.config.IQAIR_API_KEY:
            logger.warning("IQAir API key not configured")
            return None
            
        url = f"{self.config.IQAIR_BASE_URL}/city"
        params = {
            'city': city,
            'key': self.config.IQAIR_API_KEY
        }
        if country:
            params['country'] = country
        
        data = self.make_request(url, params)
        if not data or data.get('status') != 'success':
            return None
        
        result = data.get('data', {})
        current = result.get('current', {})
        pollution = current.get('pollution', {})
        weather = current.get('weather', {})
        
        return {
            'city': result.get('city'),
            'country': result.get('country'),
            'latitude': result['location']['coordinates'][1] if result.get('location') else None,
            'longitude': result['location']['coordinates'][0] if result.get('location') else None,
            'timestamp': pollution.get('ts'),
            'aqi': pollution.get('aqius'),
            'main_pollutant': pollution.get('mainus'),
            'temperature': weather.get('tp'),
            'humidity': weather.get('hu'),
            'pressure': weather.get('pr'),
            'wind_speed': weather.get('ws'),
            'source': 'iqair'
        }

class SimulatedDataGenerator:
    """Generate simulated air quality data for testing"""
    
    def __init__(self):
        self.config = Config()
        import random
        self.random = random
        
    def generate_measurement(self, city: str) -> Dict[str, Any]:
        """Generate simulated air quality measurement"""
        coords = self.config.get_city_coordinates().get(city, {'lat': 0, 'lon': 0})
        
        # Generate realistic values with some randomness
        base_pm25 = {
            'New York': 15, 'Los Angeles': 25, 'Chicago': 12,
            'London': 18, 'Paris': 20, 'Tokyo': 30,
            'Delhi': 80, 'Beijing': 60
        }.get(city, 20)
        
        pm25 = max(0, self.random.gauss(base_pm25, base_pm25 * 0.3))
        pm10 = pm25 * self.random.uniform(1.5, 2.5)
        
        return {
            'city': city,
            'country': 'Simulated',
            'latitude': coords['lat'],
            'longitude': coords['lon'],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'pm25': round(pm25, 2),
            'pm10': round(pm10, 2),
            'co': round(self.random.uniform(0.1, 2.0), 2),
            'no2': round(self.random.uniform(10, 50), 2),
            'o3': round(self.random.uniform(20, 100), 2),
            'so2': round(self.random.uniform(1, 20), 2),
            'aqi': None,  # Will be calculated
            'aqi_category': None,
            'source': 'simulated'
        }

class AirQualityDataCollector:
    """Main class for collecting air quality data from multiple sources"""
    
    def __init__(self):
        self.openaq = OpenAQAPI()
        self.iqair = IQAirAPI()
        self.simulator = SimulatedDataGenerator()
        self.config = Config()
    
    def normalize_measurement(self, measurement: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize measurement data from different sources"""
        normalized = {
            'city': measurement.get('city'),
            'country': measurement.get('country'),
            'latitude': measurement.get('latitude'),
            'longitude': measurement.get('longitude'),
            'timestamp': measurement.get('timestamp'),
            'pm25': None,
            'pm10': None,
            'co': None,
            'no2': None,
            'o3': None,
            'so2': None,
            'aqi': measurement.get('aqi'),
            'aqi_category': measurement.get('aqi_category'),
            'source': measurement.get('source')
        }
        
        # Handle OpenAQ format
        if measurement.get('source') == 'openaq':
            param = measurement.get('parameter', '').lower()
            value = measurement.get('value')
            if param in normalized and value is not None:
                normalized[param] = value
        
        # Handle IQAir format
        elif measurement.get('source') == 'iqair':
            if measurement.get('aqi'):
                normalized['aqi'] = measurement['aqi']
                normalized['aqi_category'] = self.openaq.get_aqi_category(measurement['aqi'])
        
        # Handle simulated data
        elif measurement.get('source') == 'simulated':
            for key in ['pm25', 'pm10', 'co', 'no2', 'o3', 'so2']:
                if key in measurement:
                    normalized[key] = measurement[key]
        
        # Calculate AQI if not provided
        if not normalized.get('aqi') and normalized.get('pm25'):
            aqi, category = self.openaq.calculate_aqi('pm2.5', normalized['pm25'])
            normalized['aqi'] = aqi
            normalized['aqi_category'] = category
        
        return normalized
    
    def collect_city_data(self, city: str) -> List[Dict[str, Any]]:
        """Collect air quality data for a specific city from all sources"""
        all_measurements = []
        
        logger.info(f"Collecting data for {city}")
        
        # Try OpenAQ first
        try:
            openaq_data = self.openaq.get_latest_measurements(city)
            for measurement in openaq_data:
                normalized = self.normalize_measurement(measurement)
                if normalized['city']:
                    all_measurements.append(normalized)
        except Exception as e:
            logger.error(f"OpenAQ data collection failed for {city}: {e}")
        
        # Try IQAir
        try:
            iqair_data = self.iqair.get_city_data(city)
            if iqair_data:
                normalized = self.normalize_measurement(iqair_data)
                if normalized['city']:
                    all_measurements.append(normalized)
        except Exception as e:
            logger.error(f"IQAir data collection failed for {city}: {e}")
        
        # If no real data available, generate simulated data
        if not all_measurements:
            logger.info(f"No real data available for {city}, generating simulated data")
            simulated = self.simulator.generate_measurement(city)
            normalized = self.normalize_measurement(simulated)
            all_measurements.append(normalized)
        
        return all_measurements
    
    def collect_all_cities(self) -> List[Dict[str, Any]]:
        """Collect air quality data for all monitored cities"""
        all_data = []
        
        for city in self.config.MONITORED_CITIES:
            city = city.strip()
            measurements = self.collect_city_data(city)
            all_data.extend(measurements)
            
            # Rate limiting
            time.sleep(self.config.REQUEST_DELAY)
        
        logger.info(f"Collected {len(all_data)} measurements from all cities")
        return all_data