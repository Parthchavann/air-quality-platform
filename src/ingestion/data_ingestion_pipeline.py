#!/usr/bin/env python3
"""
Main data ingestion pipeline for air quality and weather data
"""

import logging
import time
import schedule
import signal
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any
import threading

from air_quality_apis import AirQualityDataCollector
from weather_apis import WeatherDataCollector
from kafka_producer import AirQualityKafkaProducer, AlertGenerator, create_kafka_topics
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data_ingestion.log')
    ]
)
logger = logging.getLogger(__name__)

class DataIngestionPipeline:
    """Main pipeline for ingesting air quality and weather data"""
    
    def __init__(self):
        self.config = Config()
        self.air_quality_collector = AirQualityDataCollector()
        self.weather_collector = WeatherDataCollector()
        self.kafka_producer = AirQualityKafkaProducer()
        self.alert_generator = AlertGenerator()
        self.running = True
        
        # Statistics
        self.stats = {
            'air_quality_records': 0,
            'weather_records': 0,
            'alerts_generated': 0,
            'last_run': None,
            'errors': 0
        }
        
        logger.info("Data ingestion pipeline initialized")
    
    def collect_and_send_air_quality_data(self) -> bool:
        """Collect air quality data and send to Kafka"""
        try:
            logger.info("Starting air quality data collection")
            
            # Collect air quality data
            air_quality_data = self.air_quality_collector.collect_all_cities()
            
            if not air_quality_data:
                logger.warning("No air quality data collected")
                return False
            
            # Generate alerts based on thresholds
            alerts = []
            for measurement in air_quality_data:
                measurement_alerts = self.alert_generator.check_thresholds(measurement)
                alerts.extend(measurement_alerts)
            
            # Send to Kafka
            success = self.kafka_producer.send_air_quality_data(air_quality_data)
            
            # Send alerts if any
            if alerts:
                for alert in alerts:
                    self.kafka_producer.send_alert(alert)
                self.stats['alerts_generated'] += len(alerts)
                logger.info(f"Generated {len(alerts)} pollution alerts")
            
            if success:
                self.stats['air_quality_records'] += len(air_quality_data)
                logger.info(f"Successfully processed {len(air_quality_data)} air quality measurements")
                return True
            else:
                logger.error("Failed to send air quality data to Kafka")
                self.stats['errors'] += 1
                return False
                
        except Exception as e:
            logger.error(f"Error in air quality data collection: {e}")
            self.stats['errors'] += 1
            return False
    
    def collect_and_send_weather_data(self) -> bool:
        """Collect weather data and send to Kafka"""
        try:
            logger.info("Starting weather data collection")
            
            # Collect weather data
            weather_data = self.weather_collector.collect_all_cities_weather()
            
            if not weather_data:
                logger.warning("No weather data collected")
                return False
            
            # Send to Kafka
            success = self.kafka_producer.send_weather_data(weather_data)
            
            if success:
                self.stats['weather_records'] += len(weather_data)
                logger.info(f"Successfully processed {len(weather_data)} weather measurements")
                return True
            else:
                logger.error("Failed to send weather data to Kafka")
                self.stats['errors'] += 1
                return False
                
        except Exception as e:
            logger.error(f"Error in weather data collection: {e}")
            self.stats['errors'] += 1
            return False
    
    def run_collection_cycle(self):
        """Run a complete data collection cycle"""
        logger.info("=== Starting data collection cycle ===")
        start_time = datetime.now()
        
        try:
            # Collect air quality data
            aq_success = self.collect_and_send_air_quality_data()
            
            # Small delay between collections
            time.sleep(2)
            
            # Collect weather data
            weather_success = self.collect_and_send_weather_data()
            
            # Update statistics
            self.stats['last_run'] = datetime.now(timezone.utc).isoformat()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"=== Collection cycle completed in {duration:.2f} seconds ===")
            logger.info(f"Air Quality: {'✓' if aq_success else '✗'}, Weather: {'✓' if weather_success else '✗'}")
            
            return aq_success and weather_success
            
        except Exception as e:
            logger.error(f"Error in collection cycle: {e}")
            self.stats['errors'] += 1
            return False
    
    def print_statistics(self):
        """Print pipeline statistics"""
        logger.info("=== Pipeline Statistics ===")
        logger.info(f"Air Quality Records: {self.stats['air_quality_records']}")
        logger.info(f"Weather Records: {self.stats['weather_records']}")
        logger.info(f"Alerts Generated: {self.stats['alerts_generated']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"Last Run: {self.stats['last_run']}")
        logger.info("=" * 28)
    
    def run_scheduled(self):
        """Run pipeline on a schedule"""
        logger.info(f"Scheduling data collection every {self.config.INGESTION_INTERVAL} seconds")
        
        # Schedule the collection
        schedule.every(self.config.INGESTION_INTERVAL).seconds.do(self.run_collection_cycle)
        
        # Schedule statistics printing every hour
        schedule.every(1).hours.do(self.print_statistics)
        
        # Run initial collection
        self.run_collection_cycle()
        
        # Keep running scheduled jobs
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
                self.shutdown()
                break
            except Exception as e:
                logger.error(f"Error in scheduled execution: {e}")
                time.sleep(10)  # Wait before retrying
    
    def run_once(self):
        """Run pipeline once and exit"""
        logger.info("Running data collection once")
        success = self.run_collection_cycle()
        self.print_statistics()
        return success
    
    def run_continuous(self, interval: int = None):
        """Run pipeline continuously with specified interval"""
        interval = interval or self.config.INGESTION_INTERVAL
        logger.info(f"Running data collection continuously every {interval} seconds")
        
        try:
            while self.running:
                self.run_collection_cycle()
                self.print_statistics()
                
                if self.running:  # Check if still running before sleeping
                    logger.info(f"Waiting {interval} seconds before next collection...")
                    time.sleep(interval)
                    
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
            self.shutdown()
    
    def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down data ingestion pipeline...")
        self.running = False
        
        # Close Kafka producer
        if self.kafka_producer:
            self.kafka_producer.close()
        
        self.print_statistics()
        logger.info("Pipeline shutdown complete")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    global pipeline
    if pipeline:
        pipeline.shutdown()
    sys.exit(0)

def main():
    """Main entry point"""
    global pipeline
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create Kafka topics
    create_kafka_topics()
    
    # Initialize pipeline
    pipeline = DataIngestionPipeline()
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Air Quality Data Ingestion Pipeline')
    parser.add_argument('--mode', choices=['once', 'continuous', 'scheduled'], 
                       default='scheduled', help='Execution mode')
    parser.add_argument('--interval', type=int, default=None, 
                       help='Collection interval in seconds (for continuous mode)')
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'once':
            success = pipeline.run_once()
            sys.exit(0 if success else 1)
        elif args.mode == 'continuous':
            pipeline.run_continuous(args.interval)
        else:  # scheduled
            pipeline.run_scheduled()
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        if pipeline:
            pipeline.shutdown()

if __name__ == "__main__":
    main()