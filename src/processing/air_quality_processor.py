#!/usr/bin/env python3
"""
Spark Structured Streaming processor for air quality data
"""

import logging
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import json
import sys
import signal
from typing import Optional

from spark_config import create_spark_session, get_kafka_stream_reader, write_to_delta, write_stream_to_postgres, SparkConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AirQualityProcessor:
    """Spark Structured Streaming processor for air quality data"""
    
    def __init__(self):
        self.config = SparkConfig()
        self.spark = create_spark_session("AirQualityProcessor")
        self.streaming_queries = []
        
        # Define schemas
        self.air_quality_schema = self._define_air_quality_schema()
        self.weather_schema = self._define_weather_schema()
        self.alerts_schema = self._define_alerts_schema()
        
        logger.info("Air Quality Processor initialized")
    
    def _define_air_quality_schema(self) -> StructType:
        """Define schema for air quality data"""
        return StructType([
            StructField("city", StringType(), True),
            StructField("country", StringType(), True),
            StructField("latitude", DoubleType(), True),
            StructField("longitude", DoubleType(), True),
            StructField("timestamp", StringType(), True),
            StructField("pm25", DoubleType(), True),
            StructField("pm10", DoubleType(), True),
            StructField("co", DoubleType(), True),
            StructField("no2", DoubleType(), True),
            StructField("o3", DoubleType(), True),
            StructField("so2", DoubleType(), True),
            StructField("aqi", IntegerType(), True),
            StructField("aqi_category", StringType(), True),
            StructField("source", StringType(), True),
            StructField("ingestion_timestamp", StringType(), True),
            StructField("data_type", StringType(), True)
        ])
    
    def _define_weather_schema(self) -> StructType:
        """Define schema for weather data"""
        return StructType([
            StructField("city", StringType(), True),
            StructField("country", StringType(), True),
            StructField("latitude", DoubleType(), True),
            StructField("longitude", DoubleType(), True),
            StructField("timestamp", StringType(), True),
            StructField("temperature", DoubleType(), True),
            StructField("feels_like", DoubleType(), True),
            StructField("humidity", DoubleType(), True),
            StructField("pressure", DoubleType(), True),
            StructField("wind_speed", DoubleType(), True),
            StructField("wind_direction", IntegerType(), True),
            StructField("clouds", IntegerType(), True),
            StructField("visibility", IntegerType(), True),
            StructField("description", StringType(), True),
            StructField("weather_main", StringType(), True),
            StructField("source", StringType(), True),
            StructField("ingestion_timestamp", StringType(), True),
            StructField("data_type", StringType(), True)
        ])
    
    def _define_alerts_schema(self) -> StructType:
        """Define schema for alerts data"""
        return StructType([
            StructField("city", StringType(), True),
            StructField("alert_type", StringType(), True),
            StructField("severity", StringType(), True),
            StructField("pollutant", StringType(), True),
            StructField("value", DoubleType(), True),
            StructField("threshold", DoubleType(), True),
            StructField("message", StringType(), True),
            StructField("timestamp", StringType(), True),
            StructField("acknowledged", BooleanType(), True),
            StructField("ingestion_timestamp", StringType(), True),
            StructField("data_type", StringType(), True)
        ])
    
    def process_air_quality_stream(self):
        """Process air quality data stream"""
        logger.info("Starting air quality stream processing")
        
        # Read from Kafka
        raw_stream = get_kafka_stream_reader(
            self.spark, 
            self.config.KAFKA_TOPIC_AIR_QUALITY,
            "latest"
        ).load()
        
        # Parse JSON and apply schema
        parsed_stream = raw_stream.select(
            col("key").cast("string").alias("message_key"),
            col("value").cast("string").alias("json_data"),
            col("timestamp").alias("kafka_timestamp"),
            col("partition"),
            col("offset")
        ).select(
            col("message_key"),
            from_json(col("json_data"), self.air_quality_schema).alias("data"),
            col("kafka_timestamp"),
            col("partition"),
            col("offset")
        ).select(
            col("message_key"),
            col("data.*"),
            col("kafka_timestamp"),
            col("partition"),
            col("offset")
        )
        
        # Add processing timestamp and validate data
        processed_stream = parsed_stream.select(
            col("city"),
            col("country"),
            col("latitude"),
            col("longitude"),
            to_timestamp(col("timestamp")).alias("measurement_timestamp"),
            col("pm25"),
            col("pm10"),
            col("co"),
            col("no2"),
            col("o3"),
            col("so2"),
            col("aqi"),
            col("aqi_category"),
            col("source"),
            to_timestamp(col("ingestion_timestamp")).alias("ingestion_timestamp"),
            current_timestamp().alias("processing_timestamp"),
            col("kafka_timestamp"),
            col("partition"),
            col("offset")
        ).filter(
            col("city").isNotNull() & 
            col("measurement_timestamp").isNotNull()
        )
        
        # Write to Delta Lake
        delta_query = write_to_delta(
            processed_stream,
            "air_quality_measurements",
            checkpoint_location=f"{self.config.CHECKPOINT_DIR}/air_quality_delta"
        ).trigger(processingTime='30 seconds') \
         .start()
        
        self.streaming_queries.append(delta_query)
        
        # Write to PostgreSQL (for dashboard queries)
        postgres_stream = processed_stream.select(
            col("city"),
            col("country"), 
            col("latitude"),
            col("longitude"),
            col("measurement_timestamp").alias("timestamp"),
            col("pm25"),
            col("pm10"),
            col("co"),
            col("no2"),
            col("o3"),
            col("so2"),
            col("aqi"),
            col("aqi_category"),
            col("source")
        )
        
        postgres_query = write_stream_to_postgres(
            postgres_stream,
            "air_quality_measurements",
            f"{self.config.CHECKPOINT_DIR}/air_quality_postgres"
        ).start()
        
        self.streaming_queries.append(postgres_query)
        
        # Create hourly aggregations
        self._create_hourly_aggregations(processed_stream)
        
        logger.info("Air quality stream processing started")
    
    def process_weather_stream(self):
        """Process weather data stream"""
        logger.info("Starting weather stream processing")
        
        # Read from Kafka
        raw_stream = get_kafka_stream_reader(
            self.spark,
            self.config.KAFKA_TOPIC_WEATHER,
            "latest"
        ).load()
        
        # Parse JSON and apply schema
        parsed_stream = raw_stream.select(
            col("key").cast("string").alias("message_key"),
            col("value").cast("string").alias("json_data"),
            col("timestamp").alias("kafka_timestamp")
        ).select(
            col("message_key"),
            from_json(col("json_data"), self.weather_schema).alias("data"),
            col("kafka_timestamp")
        ).select(
            col("message_key"),
            col("data.*"),
            col("kafka_timestamp")
        )
        
        # Process and validate
        processed_stream = parsed_stream.select(
            col("city"),
            col("country"),
            col("latitude"),
            col("longitude"),
            to_timestamp(col("timestamp")).alias("measurement_timestamp"),
            col("temperature"),
            col("feels_like"),
            col("humidity"),
            col("pressure"),
            col("wind_speed"),
            col("wind_direction"),
            col("clouds"),
            col("visibility"),
            col("description"),
            col("weather_main"),
            col("source"),
            to_timestamp(col("ingestion_timestamp")).alias("ingestion_timestamp"),
            current_timestamp().alias("processing_timestamp")
        ).filter(
            col("city").isNotNull() & 
            col("measurement_timestamp").isNotNull()
        )
        
        # Write to Delta Lake
        delta_query = write_to_delta(
            processed_stream,
            "weather_data",
            checkpoint_location=f"{self.config.CHECKPOINT_DIR}/weather_delta"
        ).trigger(processingTime='30 seconds') \
         .start()
        
        self.streaming_queries.append(delta_query)
        
        # Write to PostgreSQL
        postgres_stream = processed_stream.select(
            col("city"),
            col("country"),
            col("latitude"),
            col("longitude"),
            col("measurement_timestamp").alias("timestamp"),
            col("temperature"),
            col("humidity"),
            col("pressure"),
            col("wind_speed"),
            col("wind_direction"),
            col("clouds"),
            col("description")
        )
        
        postgres_query = write_stream_to_postgres(
            postgres_stream,
            "weather_data",
            f"{self.config.CHECKPOINT_DIR}/weather_postgres"
        ).start()
        
        self.streaming_queries.append(postgres_query)
        
        logger.info("Weather stream processing started")
    
    def process_alerts_stream(self):
        """Process alerts stream"""
        logger.info("Starting alerts stream processing")
        
        # Read from Kafka
        raw_stream = get_kafka_stream_reader(
            self.spark,
            self.config.KAFKA_TOPIC_ALERTS,
            "latest"
        ).load()
        
        # Parse JSON and apply schema
        parsed_stream = raw_stream.select(
            col("key").cast("string").alias("message_key"),
            col("value").cast("string").alias("json_data"),
            col("timestamp").alias("kafka_timestamp")
        ).select(
            col("message_key"),
            from_json(col("json_data"), self.alerts_schema).alias("data"),
            col("kafka_timestamp")
        ).select(
            col("message_key"),
            col("data.*"),
            col("kafka_timestamp")
        )
        
        # Process alerts
        processed_stream = parsed_stream.select(
            col("city"),
            col("alert_type"),
            col("severity"),
            col("pollutant"),
            col("value"),
            col("threshold"),
            col("message"),
            to_timestamp(col("timestamp")).alias("alert_timestamp"),
            col("acknowledged"),
            to_timestamp(col("ingestion_timestamp")).alias("ingestion_timestamp"),
            current_timestamp().alias("processing_timestamp")
        ).filter(
            col("city").isNotNull() & 
            col("alert_timestamp").isNotNull()
        )
        
        # Write to PostgreSQL
        postgres_query = write_stream_to_postgres(
            processed_stream.select(
                col("city"),
                col("alert_type"),
                col("severity"),
                col("pollutant"),
                col("value"),
                col("threshold"),
                col("message"),
                col("alert_timestamp").alias("timestamp"),
                col("acknowledged")
            ),
            "pollution_alerts",
            f"{self.config.CHECKPOINT_DIR}/alerts_postgres"
        ).start()
        
        self.streaming_queries.append(postgres_query)
        
        logger.info("Alerts stream processing started")
    
    def _create_hourly_aggregations(self, air_quality_stream):
        """Create hourly aggregations for dashboard performance"""
        # Group by city and hour, calculate aggregates
        hourly_agg = air_quality_stream \
            .withWatermark("measurement_timestamp", "10 minutes") \
            .groupBy(
                col("city"),
                window(col("measurement_timestamp"), "1 hour").alias("window")
            ).agg(
                avg("pm25").alias("avg_pm25"),
                avg("pm10").alias("avg_pm10"),
                avg("co").alias("avg_co"),
                avg("no2").alias("avg_no2"),
                avg("o3").alias("avg_o3"),
                avg("so2").alias("avg_so2"),
                avg("aqi").cast("int").alias("avg_aqi"),
                max("aqi").alias("max_aqi"),
                min("aqi").alias("min_aqi"),
                count("*").alias("measurement_count")
            ).select(
                col("city"),
                col("window.start").alias("hour_timestamp"),
                col("avg_pm25"),
                col("avg_pm10"),
                col("avg_co"),
                col("avg_no2"),
                col("avg_o3"),
                col("avg_so2"),
                col("avg_aqi"),
                col("max_aqi"),
                col("min_aqi"),
                col("measurement_count")
            )
        
        # Write hourly aggregations to PostgreSQL
        hourly_query = write_stream_to_postgres(
            hourly_agg,
            "air_quality_hourly",
            f"{self.config.CHECKPOINT_DIR}/hourly_agg"
        ).outputMode("update") \
         .trigger(processingTime='60 seconds') \
         .start()
        
        self.streaming_queries.append(hourly_query)
    
    def start_processing(self):
        """Start all stream processing"""
        logger.info("Starting all stream processors...")
        
        try:
            # Start processing streams
            self.process_air_quality_stream()
            self.process_weather_stream()
            self.process_alerts_stream()
            
            logger.info(f"Started {len(self.streaming_queries)} streaming queries")
            
            # Wait for termination
            for query in self.streaming_queries:
                logger.info(f"Query {query.name}: {query.status}")
            
        except Exception as e:
            logger.error(f"Error starting stream processing: {e}")
            self.stop_processing()
            raise
    
    def stop_processing(self):
        """Stop all stream processing"""
        logger.info("Stopping all stream processors...")
        
        for query in self.streaming_queries:
            try:
                if query.isActive:
                    query.stop()
                    logger.info(f"Stopped query: {query.name}")
            except Exception as e:
                logger.error(f"Error stopping query {query.name}: {e}")
        
        if self.spark:
            self.spark.stop()
            logger.info("Spark session stopped")
    
    def await_termination(self):
        """Wait for all queries to terminate"""
        try:
            for query in self.streaming_queries:
                query.awaitTermination()
        except KeyboardInterrupt:
            logger.info("Received interrupt, stopping processing...")
            self.stop_processing()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    global processor
    if processor:
        processor.stop_processing()
    sys.exit(0)

def main():
    """Main entry point"""
    global processor
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create processor
    processor = AirQualityProcessor()
    
    try:
        # Start processing
        processor.start_processing()
        
        # Keep running
        processor.await_termination()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        if processor:
            processor.stop_processing()

if __name__ == "__main__":
    main()