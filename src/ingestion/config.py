import os
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

class Config:
    # API Keys
    OPENAQ_API_KEY = os.getenv('OPENAQ_API_KEY')
    IQAIR_API_KEY = os.getenv('IQAIR_API_KEY')
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    KAFKA_TOPIC_AIR_QUALITY = os.getenv('KAFKA_TOPIC_AIR_QUALITY', 'air-quality-stream')
    KAFKA_TOPIC_WEATHER = os.getenv('KAFKA_TOPIC_WEATHER', 'weather-stream')
    KAFKA_TOPIC_ALERTS = os.getenv('KAFKA_TOPIC_ALERTS', 'pollution-alerts')
    
    # Database Configuration
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'airquality')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'airquality_user')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'secure_password')
    
    # Cities to monitor
    MONITORED_CITIES = os.getenv('MONITORED_CITIES', 'New York,Los Angeles,Chicago,London,Paris,Tokyo,Delhi,Beijing').split(',')
    
    # API Base URLs
    OPENAQ_BASE_URL = "https://api.openaq.org/v2"
    IQAIR_BASE_URL = "https://api.airvisual.com/v2"
    OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    # Rate limiting
    REQUEST_DELAY = 1  # seconds between API requests
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds
    
    # Data ingestion settings
    INGESTION_INTERVAL = 300  # 5 minutes in seconds
    BATCH_SIZE = 100
    
    @property
    def postgres_url(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @classmethod
    def get_city_coordinates(cls) -> Dict[str, Dict[str, float]]:
        """Predefined coordinates for cities"""
        return {
            'New York': {'lat': 40.7128, 'lon': -74.0060},
            'Los Angeles': {'lat': 34.0522, 'lon': -118.2437},
            'Chicago': {'lat': 41.8781, 'lon': -87.6298},
            'London': {'lat': 51.5074, 'lon': -0.1278},
            'Paris': {'lat': 48.8566, 'lon': 2.3522},
            'Tokyo': {'lat': 35.6762, 'lon': 139.6503},
            'Delhi': {'lat': 28.6139, 'lon': 77.2090},
            'Beijing': {'lat': 39.9042, 'lon': 116.4074}
        }