import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError
import time
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AirQualityKafkaProducer:
    """Kafka producer for air quality and weather data"""
    
    def __init__(self):
        self.config = Config()
        self.producer = None
        self._connect()
    
    def _connect(self):
        """Connect to Kafka broker"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.config.KAFKA_BOOTSTRAP_SERVERS.split(','),
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: str(k).encode('utf-8') if k else None,
                retries=3,
                retry_backoff_ms=1000,
                acks='all',
                compression_type='gzip',
                batch_size=16384,
                linger_ms=10,
                buffer_memory=33554432
            )
            logger.info(f"Connected to Kafka brokers: {self.config.KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise
    
    def send_air_quality_data(self, data: List[Dict[str, Any]]) -> bool:
        """Send air quality data to Kafka topic"""
        if not self.producer:
            logger.error("Kafka producer not initialized")
            return False
        
        success_count = 0
        
        for measurement in data:
            try:
                # Add metadata
                enriched_measurement = {
                    **measurement,
                    'ingestion_timestamp': datetime.now(timezone.utc).isoformat(),
                    'data_type': 'air_quality'
                }
                
                # Use city as key for partitioning
                key = measurement.get('city')
                
                future = self.producer.send(
                    self.config.KAFKA_TOPIC_AIR_QUALITY,
                    key=key,
                    value=enriched_measurement
                )
                
                # Wait for the message to be sent (with timeout)
                record_metadata = future.get(timeout=10)
                success_count += 1
                
                logger.debug(f"Sent air quality data for {key} to partition {record_metadata.partition}")
                
            except KafkaError as e:
                logger.error(f"Failed to send air quality data: {e}")
            except Exception as e:
                logger.error(f"Unexpected error sending air quality data: {e}")
        
        # Ensure all messages are sent
        self.producer.flush()
        
        logger.info(f"Successfully sent {success_count}/{len(data)} air quality measurements to Kafka")
        return success_count == len(data)
    
    def send_weather_data(self, data: List[Dict[str, Any]]) -> bool:
        """Send weather data to Kafka topic"""
        if not self.producer:
            logger.error("Kafka producer not initialized")
            return False
        
        success_count = 0
        
        for weather_measurement in data:
            try:
                # Add metadata
                enriched_measurement = {
                    **weather_measurement,
                    'ingestion_timestamp': datetime.now(timezone.utc).isoformat(),
                    'data_type': 'weather'
                }
                
                # Use city as key for partitioning
                key = weather_measurement.get('city')
                
                future = self.producer.send(
                    self.config.KAFKA_TOPIC_WEATHER,
                    key=key,
                    value=enriched_measurement
                )
                
                # Wait for the message to be sent
                record_metadata = future.get(timeout=10)
                success_count += 1
                
                logger.debug(f"Sent weather data for {key} to partition {record_metadata.partition}")
                
            except KafkaError as e:
                logger.error(f"Failed to send weather data: {e}")
            except Exception as e:
                logger.error(f"Unexpected error sending weather data: {e}")
        
        # Ensure all messages are sent
        self.producer.flush()
        
        logger.info(f"Successfully sent {success_count}/{len(data)} weather measurements to Kafka")
        return success_count == len(data)
    
    def send_alert(self, alert: Dict[str, Any]) -> bool:
        """Send pollution alert to Kafka topic"""
        if not self.producer:
            logger.error("Kafka producer not initialized")
            return False
        
        try:
            # Add metadata
            enriched_alert = {
                **alert,
                'ingestion_timestamp': datetime.now(timezone.utc).isoformat(),
                'data_type': 'alert'
            }
            
            # Use city as key for partitioning
            key = alert.get('city')
            
            future = self.producer.send(
                self.config.KAFKA_TOPIC_ALERTS,
                key=key,
                value=enriched_alert
            )
            
            # Wait for the message to be sent
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Sent alert for {key} to partition {record_metadata.partition}")
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send alert: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending alert: {e}")
            return False
    
    def close(self):
        """Close the Kafka producer"""
        if self.producer:
            try:
                self.producer.flush()
                self.producer.close()
                logger.info("Kafka producer closed successfully")
            except Exception as e:
                logger.error(f"Error closing Kafka producer: {e}")

class AlertGenerator:
    """Generate pollution alerts based on thresholds"""
    
    def __init__(self):
        self.config = Config()
    
    def check_thresholds(self, measurement: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check if measurement exceeds pollution thresholds"""
        alerts = []
        city = measurement.get('city')
        
        if not city:
            return alerts
        
        # Default thresholds (can be customized per city)
        thresholds = {
            'pm25': {'warning': 35, 'alert': 55, 'critical': 150},
            'pm10': {'warning': 54, 'alert': 154, 'critical': 354},
            'aqi': {'warning': 100, 'alert': 150, 'critical': 200},
            'no2': {'warning': 100, 'alert': 200, 'critical': 400},
            'o3': {'warning': 70, 'alert': 105, 'critical': 200},
            'co': {'warning': 9, 'alert': 15, 'critical': 30}
        }
        
        timestamp = measurement.get('timestamp') or datetime.now(timezone.utc).isoformat()
        
        for pollutant, levels in thresholds.items():
            value = measurement.get(pollutant)
            
            if value is None:
                continue
            
            severity = None
            threshold = None
            
            if value >= levels['critical']:
                severity = 'critical'
                threshold = levels['critical']
            elif value >= levels['alert']:
                severity = 'alert'
                threshold = levels['alert']
            elif value >= levels['warning']:
                severity = 'warning'
                threshold = levels['warning']
            
            if severity:
                alert = {
                    'city': city,
                    'alert_type': 'pollution_threshold',
                    'severity': severity,
                    'pollutant': pollutant,
                    'value': value,
                    'threshold': threshold,
                    'message': self._generate_alert_message(city, pollutant, value, severity),
                    'timestamp': timestamp,
                    'acknowledged': False
                }
                alerts.append(alert)
        
        return alerts
    
    def _generate_alert_message(self, city: str, pollutant: str, value: float, severity: str) -> str:
        """Generate human-readable alert message"""
        pollutant_names = {
            'pm25': 'PM2.5',
            'pm10': 'PM10',
            'aqi': 'Air Quality Index',
            'no2': 'Nitrogen Dioxide',
            'o3': 'Ozone',
            'co': 'Carbon Monoxide'
        }
        
        pollutant_display = pollutant_names.get(pollutant, pollutant.upper())
        
        severity_messages = {
            'warning': f"Elevated {pollutant_display} levels detected in {city}. Current level: {value}. Consider limiting outdoor activities for sensitive individuals.",
            'alert': f"High {pollutant_display} levels detected in {city}. Current level: {value}. Limit outdoor activities and consider wearing masks.",
            'critical': f"CRITICAL: Very high {pollutant_display} levels detected in {city}. Current level: {value}. Avoid outdoor activities and stay indoors."
        }
        
        return severity_messages.get(severity, f"{severity.upper()}: {pollutant_display} level {value} detected in {city}")

def create_kafka_topics():
    """Create Kafka topics if they don't exist"""
    try:
        from kafka.admin import KafkaAdminClient, NewTopic
        
        config = Config()
        admin_client = KafkaAdminClient(
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS.split(',')
        )
        
        topics = [
            NewTopic(name=config.KAFKA_TOPIC_AIR_QUALITY, num_partitions=3, replication_factor=1),
            NewTopic(name=config.KAFKA_TOPIC_WEATHER, num_partitions=3, replication_factor=1),
            NewTopic(name=config.KAFKA_TOPIC_ALERTS, num_partitions=1, replication_factor=1)
        ]
        
        admin_client.create_topics(topics, validate_only=False)
        logger.info("Kafka topics created successfully")
        
    except Exception as e:
        logger.info(f"Topics may already exist or failed to create: {e}")

if __name__ == "__main__":
    # Create topics when running as standalone script
    create_kafka_topics()