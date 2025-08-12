#!/usr/bin/env python3

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import psycopg2
from sqlalchemy import create_engine, text
import random
import os

def generate_sample_data():
    """Generate comprehensive sample data for the premium dashboard"""
    
    # Major cities with realistic coordinates
    cities_data = [
        {"city": "New York", "country": "USA", "latitude": 40.7128, "longitude": -74.0060, "population": 8400000},
        {"city": "Los Angeles", "country": "USA", "latitude": 34.0522, "longitude": -118.2437, "population": 4000000},
        {"city": "London", "country": "UK", "latitude": 51.5074, "longitude": -0.1278, "population": 9000000},
        {"city": "Paris", "country": "France", "latitude": 48.8566, "longitude": 2.3522, "population": 2100000},
        {"city": "Tokyo", "country": "Japan", "latitude": 35.6762, "longitude": 139.6503, "population": 14000000},
        {"city": "Beijing", "country": "China", "latitude": 39.9042, "longitude": 116.4074, "population": 21500000},
        {"city": "Mumbai", "country": "India", "latitude": 19.0760, "longitude": 72.8777, "population": 12500000},
        {"city": "Delhi", "country": "India", "latitude": 28.7041, "longitude": 77.1025, "population": 11000000},
        {"city": "São Paulo", "country": "Brazil", "latitude": -23.5505, "longitude": -46.6333, "population": 12300000},
        {"city": "Mexico City", "country": "Mexico", "latitude": 19.4326, "longitude": -99.1332, "population": 9200000},
        {"city": "Cairo", "country": "Egypt", "latitude": 30.0444, "longitude": 31.2357, "population": 10000000},
        {"city": "Sydney", "country": "Australia", "latitude": -33.8688, "longitude": 151.2093, "population": 5300000},
        {"city": "Toronto", "country": "Canada", "latitude": 43.6532, "longitude": -79.3832, "population": 2900000},
        {"city": "Berlin", "country": "Germany", "latitude": 52.5200, "longitude": 13.4050, "population": 3700000},
        {"city": "Singapore", "country": "Singapore", "latitude": 1.3521, "longitude": 103.8198, "population": 5900000}
    ]
    
    # Generate data for the last 7 days with hourly readings
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    air_quality_data = []
    weather_data = []
    pollution_alerts = []
    
    # Generate hourly data for each city
    current_time = start_time
    while current_time <= end_time:
        for city_info in cities_data:
            city = city_info["city"]
            country = city_info["country"]
            lat = city_info["latitude"]
            lon = city_info["longitude"]
            
            # Generate realistic air quality data based on city characteristics
            base_aqi = get_base_aqi_for_city(city)
            
            # Add time-based variations (worse during rush hours, better at night)
            hour = current_time.hour
            time_factor = 1.0
            if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hours
                time_factor = 1.3
            elif 22 <= hour or hour <= 5:  # Night time
                time_factor = 0.7
            
            # Add day-of-week variation (worse on weekdays)
            day_factor = 1.2 if current_time.weekday() < 5 else 0.8
            
            # Add random variation
            random_factor = random.uniform(0.8, 1.2)
            
            # Calculate final AQI
            final_aqi = max(10, min(500, base_aqi * time_factor * day_factor * random_factor))
            
            # Generate individual pollutant values based on AQI
            pm25 = max(0, final_aqi * random.uniform(0.4, 0.8))
            pm10 = max(0, pm25 * random.uniform(1.2, 2.0))
            no2 = max(0, final_aqi * random.uniform(0.3, 0.6))
            o3 = max(0, final_aqi * random.uniform(0.2, 0.5))
            co = max(0, final_aqi * random.uniform(0.05, 0.15))
            so2 = max(0, final_aqi * random.uniform(0.1, 0.3))
            
            # Determine AQI category
            aqi_category = get_aqi_category(final_aqi)
            
            air_quality_record = {
                'city': city,
                'country': country,
                'latitude': lat,
                'longitude': lon,
                'timestamp': current_time,
                'pm25': round(pm25, 1),
                'pm10': round(pm10, 1),
                'co': round(co, 2),
                'no2': round(no2, 1),
                'o3': round(o3, 1),
                'so2': round(so2, 1),
                'aqi': round(final_aqi, 0),
                'aqi_category': aqi_category,
                'source': 'sample_data'
            }
            air_quality_data.append(air_quality_record)
            
            # Generate weather data
            weather_record = generate_weather_data(city_info, current_time)
            weather_data.append(weather_record)
            
            # Generate alerts for high pollution levels
            if final_aqi > 150 and random.random() < 0.1:  # 10% chance of alert for unhealthy levels
                alert_record = generate_pollution_alert(city, final_aqi, pm25, current_time)
                pollution_alerts.append(alert_record)
        
        current_time += timedelta(hours=1)
    
    # Convert to DataFrames
    air_quality_df = pd.DataFrame(air_quality_data)
    weather_df = pd.DataFrame(weather_data)
    alerts_df = pd.DataFrame(pollution_alerts)
    
    return air_quality_df, weather_df, alerts_df

def get_base_aqi_for_city(city):
    """Get realistic base AQI values for different cities"""
    city_aqi_map = {
        "New York": 45,
        "Los Angeles": 65,
        "London": 35,
        "Paris": 40,
        "Tokyo": 50,
        "Beijing": 120,
        "Mumbai": 95,
        "Delhi": 150,
        "São Paulo": 75,
        "Mexico City": 85,
        "Cairo": 110,
        "Sydney": 25,
        "Toronto": 35,
        "Berlin": 30,
        "Singapore": 55
    }
    return city_aqi_map.get(city, 50)

def get_aqi_category(aqi):
    """Convert AQI value to category"""
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

def generate_weather_data(city_info, timestamp):
    """Generate realistic weather data"""
    city = city_info["city"]
    lat = city_info["latitude"]
    lon = city_info["longitude"]
    
    # Base temperature based on latitude and season
    base_temp = 20 - abs(lat) * 0.5  # Rough approximation
    
    # Add seasonal variation
    day_of_year = timestamp.timetuple().tm_yday
    seasonal_variation = 10 * np.sin((day_of_year - 80) * 2 * np.pi / 365)  # Peak in summer
    
    # Add daily variation
    hour_variation = 8 * np.sin((timestamp.hour - 6) * np.pi / 12)  # Peak at 2 PM
    
    temperature = base_temp + seasonal_variation + hour_variation + random.uniform(-5, 5)
    
    # Generate other weather parameters
    humidity = max(20, min(95, 60 + random.uniform(-20, 30)))
    pressure = 1013 + random.uniform(-20, 20)
    wind_speed = max(0, random.uniform(0, 25))
    wind_direction = random.uniform(0, 360)
    clouds = random.uniform(0, 100)
    
    # Simple weather description based on conditions
    if clouds < 20:
        description = "Clear sky"
    elif clouds < 50:
        description = "Partly cloudy"
    elif clouds < 80:
        description = "Cloudy"
    else:
        description = "Overcast"
    
    return {
        'city': city,
        'country': city_info["country"],
        'latitude': lat,
        'longitude': lon,
        'timestamp': timestamp,
        'temperature': round(temperature, 1),
        'humidity': round(humidity, 1),
        'pressure': round(pressure, 1),
        'wind_speed': round(wind_speed, 1),
        'wind_direction': round(wind_direction, 0),
        'clouds': round(clouds, 0),
        'description': description
    }

def generate_pollution_alert(city, aqi, pm25, timestamp):
    """Generate pollution alerts for high levels"""
    severity_map = {
        (150, 200): "MEDIUM",
        (200, 300): "HIGH", 
        (300, 500): "HIGH"
    }
    
    severity = "LOW"
    for (min_aqi, max_aqi), sev in severity_map.items():
        if min_aqi <= aqi < max_aqi:
            severity = sev
            break
    
    if aqi >= 300:
        severity = "HIGH"
    
    messages = {
        "MEDIUM": f"Air quality has reached unhealthy levels in {city}. Sensitive individuals should limit outdoor activities.",
        "HIGH": f"Air quality is very unhealthy in {city}. All individuals should avoid prolonged outdoor exposure.",
        "LOW": f"Air quality is moderately unhealthy in {city}. Monitor conditions closely."
    }
    
    return {
        'city': city,
        'alert_type': 'AQI_HIGH' if aqi > 200 else 'PM25_HIGH' if pm25 > 55 else 'MODERATE_POLLUTION',
        'severity': severity,
        'pollutant': 'AQI' if aqi > 200 else 'PM2.5',
        'value': aqi if aqi > 200 else pm25,
        'threshold': 200 if aqi > 200 else 55,
        'message': messages[severity],
        'timestamp': timestamp,
        'acknowledged': random.choice([True, False])
    }

def create_database_tables():
    """Create necessary database tables"""
    
    # Database connection parameters
    db_params = {
        'host': os.getenv('POSTGRES_HOST', 'postgres'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DB', 'airquality'),
        'user': os.getenv('POSTGRES_USER', 'airquality_user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'secure_password')
    }
    
    try:
        # Create connection
        conn_str = f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}"
        engine = create_engine(conn_str)
        
        # Create tables
        with engine.connect() as conn:
            # Air quality measurements table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS air_quality_measurements (
                    id SERIAL PRIMARY KEY,
                    city VARCHAR(100) NOT NULL,
                    country VARCHAR(100),
                    latitude FLOAT,
                    longitude FLOAT,
                    timestamp TIMESTAMP NOT NULL,
                    pm25 FLOAT,
                    pm10 FLOAT,
                    co FLOAT,
                    no2 FLOAT,
                    o3 FLOAT,
                    so2 FLOAT,
                    aqi INTEGER,
                    aqi_category VARCHAR(50),
                    source VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Weather data table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS weather_data (
                    id SERIAL PRIMARY KEY,
                    city VARCHAR(100) NOT NULL,
                    country VARCHAR(100),
                    latitude FLOAT,
                    longitude FLOAT,
                    timestamp TIMESTAMP NOT NULL,
                    temperature FLOAT,
                    humidity FLOAT,
                    pressure FLOAT,
                    wind_speed FLOAT,
                    wind_direction FLOAT,
                    clouds FLOAT,
                    description VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Pollution alerts table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS pollution_alerts (
                    id SERIAL PRIMARY KEY,
                    city VARCHAR(100) NOT NULL,
                    alert_type VARCHAR(50),
                    severity VARCHAR(20),
                    pollutant VARCHAR(20),
                    value FLOAT,
                    threshold FLOAT,
                    message TEXT,
                    timestamp TIMESTAMP NOT NULL,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # City configurations table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS city_configurations (
                    id SERIAL PRIMARY KEY,
                    city VARCHAR(100) NOT NULL,
                    country VARCHAR(100),
                    latitude FLOAT,
                    longitude FLOAT,
                    timezone VARCHAR(50),
                    population INTEGER,
                    monitoring_enabled BOOLEAN DEFAULT TRUE,
                    alert_thresholds JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            conn.commit()
            print("✅ Database tables created successfully!")
            return engine
            
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        return None

def populate_database():
    """Populate database with sample data"""
    
    # Create tables first
    engine = create_database_tables()
    if not engine:
        return
    
    print("🔄 Generating comprehensive sample data...")
    
    # Generate sample data
    air_quality_df, weather_df, alerts_df = generate_sample_data()
    
    print(f"📊 Generated {len(air_quality_df)} air quality records")
    print(f"🌤️ Generated {len(weather_df)} weather records")
    print(f"🚨 Generated {len(alerts_df)} alert records")
    
    try:
        # Insert data into database
        print("💾 Inserting data into database...")
        
        # Clear existing data
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE air_quality_measurements CASCADE"))
            conn.execute(text("TRUNCATE TABLE weather_data CASCADE"))
            conn.execute(text("TRUNCATE TABLE pollution_alerts CASCADE"))
            conn.execute(text("TRUNCATE TABLE city_configurations CASCADE"))
            conn.commit()
        
        # Insert new data
        air_quality_df.to_sql('air_quality_measurements', engine, if_exists='append', index=False, method='multi')
        weather_df.to_sql('weather_data', engine, if_exists='append', index=False, method='multi')
        if not alerts_df.empty:
            alerts_df.to_sql('pollution_alerts', engine, if_exists='append', index=False, method='multi')
        
        # Insert city configurations
        cities_config_data = [
            {
                "city": "New York", "country": "USA", "latitude": 40.7128, "longitude": -74.0060,
                "timezone": "America/New_York", "population": 8400000, "monitoring_enabled": True,
                "alert_thresholds": '{"pm25": 55, "pm10": 150, "no2": 100, "o3": 120}'
            },
            {
                "city": "Los Angeles", "country": "USA", "latitude": 34.0522, "longitude": -118.2437,
                "timezone": "America/Los_Angeles", "population": 4000000, "monitoring_enabled": True,
                "alert_thresholds": '{"pm25": 55, "pm10": 150, "no2": 100, "o3": 120}'
            },
            {
                "city": "London", "country": "UK", "latitude": 51.5074, "longitude": -0.1278,
                "timezone": "Europe/London", "population": 9000000, "monitoring_enabled": True,
                "alert_thresholds": '{"pm25": 50, "pm10": 100, "no2": 80, "o3": 100}'
            },
            {
                "city": "Delhi", "country": "India", "latitude": 28.7041, "longitude": 77.1025,
                "timezone": "Asia/Kolkata", "population": 11000000, "monitoring_enabled": True,
                "alert_thresholds": '{"pm25": 60, "pm10": 100, "no2": 80, "o3": 100}'
            },
            {
                "city": "Beijing", "country": "China", "latitude": 39.9042, "longitude": 116.4074,
                "timezone": "Asia/Shanghai", "population": 21500000, "monitoring_enabled": True,
                "alert_thresholds": '{"pm25": 75, "pm10": 150, "no2": 80, "o3": 160}'
            }
        ]
        
        cities_df = pd.DataFrame(cities_config_data)
        cities_df.to_sql('city_configurations', engine, if_exists='append', index=False, method='multi')
        
        print("✅ Sample data inserted successfully!")
        print(f"🎯 Ready to view your premium dashboard at: http://localhost:8502")
        
        # Display summary statistics
        print("\n📈 Data Summary:")
        print("-" * 50)
        print(f"🏙️  Cities: {air_quality_df['city'].nunique()}")
        print(f"📅 Date Range: {air_quality_df['timestamp'].min()} to {air_quality_df['timestamp'].max()}")
        print(f"🌍 Average Global AQI: {air_quality_df['aqi'].mean():.1f}")
        print(f"🔴 Worst AQI: {air_quality_df['aqi'].max():.0f} in {air_quality_df.loc[air_quality_df['aqi'].idxmax(), 'city']}")
        print(f"🟢 Best AQI: {air_quality_df['aqi'].min():.0f} in {air_quality_df.loc[air_quality_df['aqi'].idxmin(), 'city']}")
        print(f"🚨 Active Alerts: {len(alerts_df[alerts_df['acknowledged'] == False]) if not alerts_df.empty else 0}")
        
    except Exception as e:
        print(f"❌ Error inserting data: {e}")
        return
    
    print("\n🎉 Premium dashboard is ready with beautiful sample data!")
    print("🌐 Open http://localhost:8502 in your browser to explore!")

if __name__ == "__main__":
    populate_database()