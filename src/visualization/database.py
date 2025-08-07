import os
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import streamlit as st

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Database connection and query utilities for the dashboard"""
    
    def __init__(self):
        self.host = os.getenv('POSTGRES_HOST', 'localhost')
        self.port = os.getenv('POSTGRES_PORT', '5432')
        self.database = os.getenv('POSTGRES_DB', 'airquality')
        self.username = os.getenv('POSTGRES_USER', 'airquality_user')
        self.password = os.getenv('POSTGRES_PASSWORD', 'secure_password')
        
        self.connection_string = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        self.engine = None
        
        self._connect()
    
    def _connect(self):
        """Establish database connection"""
        try:
            self.engine = create_engine(self.connection_string)
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            st.error(f"Database connection failed: {e}")
            self.engine = None
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_latest_air_quality_data(_self, hours: int = 24) -> pd.DataFrame:
        """Get latest air quality data for all cities"""
        if not _self.engine:
            return pd.DataFrame()
        
        query = """
        SELECT 
            city,
            country,
            latitude,
            longitude,
            timestamp,
            pm25,
            pm10,
            co,
            no2,
            o3,
            so2,
            aqi,
            aqi_category,
            source
        FROM air_quality_measurements 
        WHERE timestamp >= NOW() - INTERVAL '%s hours'
        ORDER BY timestamp DESC
        """
        
        try:
            df = pd.read_sql_query(query, _self.engine, params=[hours])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        except Exception as e:
            logger.error(f"Error fetching air quality data: {e}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=300)
    def get_city_air_quality_history(_self, city: str, days: int = 7) -> pd.DataFrame:
        """Get air quality history for a specific city"""
        if not _self.engine:
            return pd.DataFrame()
        
        query = """
        SELECT 
            timestamp,
            pm25,
            pm10,
            co,
            no2,
            o3,
            so2,
            aqi,
            aqi_category
        FROM air_quality_measurements 
        WHERE city = %s 
        AND timestamp >= NOW() - INTERVAL '%s days'
        ORDER BY timestamp
        """
        
        try:
            df = pd.read_sql_query(query, _self.engine, params=[city, days])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        except Exception as e:
            logger.error(f"Error fetching city history for {city}: {e}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=300)
    def get_hourly_aggregated_data(_self, hours: int = 48) -> pd.DataFrame:
        """Get hourly aggregated data for performance"""
        if not _self.engine:
            return pd.DataFrame()
        
        query = """
        SELECT 
            city,
            hour_timestamp,
            avg_pm25,
            avg_pm10,
            avg_co,
            avg_no2,
            avg_o3,
            avg_so2,
            avg_aqi,
            max_aqi,
            min_aqi,
            measurement_count
        FROM air_quality_hourly 
        WHERE hour_timestamp >= NOW() - INTERVAL '%s hours'
        ORDER BY hour_timestamp DESC
        """
        
        try:
            df = pd.read_sql_query(query, _self.engine, params=[hours])
            df['hour_timestamp'] = pd.to_datetime(df['hour_timestamp'])
            return df
        except Exception as e:
            logger.error(f"Error fetching hourly data: {e}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=300)
    def get_weather_data(_self, hours: int = 24) -> pd.DataFrame:
        """Get weather data for all cities"""
        if not _self.engine:
            return pd.DataFrame()
        
        query = """
        SELECT 
            city,
            country,
            latitude,
            longitude,
            timestamp,
            temperature,
            humidity,
            pressure,
            wind_speed,
            wind_direction,
            clouds,
            description
        FROM weather_data 
        WHERE timestamp >= NOW() - INTERVAL '%s hours'
        ORDER BY timestamp DESC
        """
        
        try:
            df = pd.read_sql_query(query, _self.engine, params=[hours])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=60)  # Cache for 1 minute for alerts
    def get_active_alerts(_self) -> pd.DataFrame:
        """Get active pollution alerts"""
        if not _self.engine:
            return pd.DataFrame()
        
        query = """
        SELECT 
            city,
            alert_type,
            severity,
            pollutant,
            value,
            threshold,
            message,
            timestamp,
            acknowledged
        FROM pollution_alerts 
        WHERE acknowledged = false 
        AND timestamp >= NOW() - INTERVAL '24 hours'
        ORDER BY timestamp DESC
        """
        
        try:
            df = pd.read_sql_query(query, _self.engine)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        except Exception as e:
            logger.error(f"Error fetching alerts: {e}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=300)
    def get_city_configurations(_self) -> pd.DataFrame:
        """Get city configuration data"""
        if not _self.engine:
            return pd.DataFrame()
        
        query = """
        SELECT 
            city,
            country,
            latitude,
            longitude,
            timezone,
            population,
            monitoring_enabled,
            alert_thresholds
        FROM city_configurations
        WHERE monitoring_enabled = true
        ORDER BY city
        """
        
        try:
            df = pd.read_sql_query(query, _self.engine)
            return df
        except Exception as e:
            logger.error(f"Error fetching city configurations: {e}")
            return pd.DataFrame()
    
    def get_data_quality_stats(self) -> Dict[str, Any]:
        """Get data quality statistics"""
        if not self.engine:
            return {}
        
        try:
            with self.engine.connect() as conn:
                # Air quality data stats
                aq_stats = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_measurements,
                        COUNT(DISTINCT city) as cities_count,
                        MAX(timestamp) as latest_measurement,
                        MIN(timestamp) as earliest_measurement
                    FROM air_quality_measurements
                    WHERE timestamp >= NOW() - INTERVAL '24 hours'
                """)).fetchone()
                
                # Weather data stats
                weather_stats = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_measurements,
                        MAX(timestamp) as latest_measurement
                    FROM weather_data
                    WHERE timestamp >= NOW() - INTERVAL '24 hours'
                """)).fetchone()
                
                # Alert stats
                alert_stats = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_alerts,
                        COUNT(CASE WHEN acknowledged = false THEN 1 END) as active_alerts
                    FROM pollution_alerts
                    WHERE timestamp >= NOW() - INTERVAL '24 hours'
                """)).fetchone()
                
                return {
                    'air_quality': dict(aq_stats._mapping) if aq_stats else {},
                    'weather': dict(weather_stats._mapping) if weather_stats else {},
                    'alerts': dict(alert_stats._mapping) if alert_stats else {}
                }
                
        except Exception as e:
            logger.error(f"Error fetching data quality stats: {e}")
            return {}
    
    def acknowledge_alert(self, alert_id: int) -> bool:
        """Acknowledge a pollution alert"""
        if not self.engine:
            return False
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("UPDATE pollution_alerts SET acknowledged = true WHERE id = :alert_id"),
                    {"alert_id": alert_id}
                )
                conn.commit()
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"Error acknowledging alert {alert_id}: {e}")
            return False