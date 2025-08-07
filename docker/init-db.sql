-- Create airflow database
CREATE DATABASE airflow;

-- Create tables for air quality data
CREATE TABLE IF NOT EXISTS air_quality_measurements (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    timestamp TIMESTAMP NOT NULL,
    pm25 DECIMAL(10, 2),
    pm10 DECIMAL(10, 2),
    co DECIMAL(10, 2),
    no2 DECIMAL(10, 2),
    o3 DECIMAL(10, 2),
    so2 DECIMAL(10, 2),
    aqi INTEGER,
    aqi_category VARCHAR(50),
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster queries
CREATE INDEX idx_air_quality_city_timestamp ON air_quality_measurements(city, timestamp DESC);
CREATE INDEX idx_air_quality_timestamp ON air_quality_measurements(timestamp DESC);

-- Create table for weather data
CREATE TABLE IF NOT EXISTS weather_data (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    timestamp TIMESTAMP NOT NULL,
    temperature DECIMAL(5, 2),
    humidity DECIMAL(5, 2),
    pressure DECIMAL(7, 2),
    wind_speed DECIMAL(6, 2),
    wind_direction INTEGER,
    clouds INTEGER,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for weather data
CREATE INDEX idx_weather_city_timestamp ON weather_data(city, timestamp DESC);

-- Create table for pollution alerts
CREATE TABLE IF NOT EXISTS pollution_alerts (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    pollutant VARCHAR(50),
    value DECIMAL(10, 2),
    threshold DECIMAL(10, 2),
    message TEXT,
    timestamp TIMESTAMP NOT NULL,
    acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for alerts
CREATE INDEX idx_alerts_city_timestamp ON pollution_alerts(city, timestamp DESC);
CREATE INDEX idx_alerts_acknowledged ON pollution_alerts(acknowledged);

-- Create table for city configurations
CREATE TABLE IF NOT EXISTS city_configurations (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL UNIQUE,
    country VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    timezone VARCHAR(50),
    population INTEGER,
    area_km2 DECIMAL(10, 2),
    monitoring_enabled BOOLEAN DEFAULT TRUE,
    alert_thresholds JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default city configurations
INSERT INTO city_configurations (city, country, latitude, longitude, timezone, population, monitoring_enabled, alert_thresholds)
VALUES 
    ('New York', 'USA', 40.7128, -74.0060, 'America/New_York', 8336000, true, 
     '{"pm25": {"warning": 35, "alert": 55, "critical": 150}, "aqi": {"warning": 100, "alert": 150, "critical": 200}}'),
    ('Los Angeles', 'USA', 34.0522, -118.2437, 'America/Los_Angeles', 3899000, true,
     '{"pm25": {"warning": 35, "alert": 55, "critical": 150}, "aqi": {"warning": 100, "alert": 150, "critical": 200}}'),
    ('Chicago', 'USA', 41.8781, -87.6298, 'America/Chicago', 2716000, true,
     '{"pm25": {"warning": 35, "alert": 55, "critical": 150}, "aqi": {"warning": 100, "alert": 150, "critical": 200}}'),
    ('London', 'UK', 51.5074, -0.1278, 'Europe/London', 8982000, true,
     '{"pm25": {"warning": 25, "alert": 40, "critical": 100}, "aqi": {"warning": 100, "alert": 150, "critical": 200}}'),
    ('Paris', 'France', 48.8566, 2.3522, 'Europe/Paris', 2161000, true,
     '{"pm25": {"warning": 25, "alert": 40, "critical": 100}, "aqi": {"warning": 100, "alert": 150, "critical": 200}}'),
    ('Tokyo', 'Japan', 35.6762, 139.6503, 'Asia/Tokyo', 13960000, true,
     '{"pm25": {"warning": 35, "alert": 75, "critical": 150}, "aqi": {"warning": 100, "alert": 150, "critical": 200}}'),
    ('Delhi', 'India', 28.6139, 77.2090, 'Asia/Kolkata', 32940000, true,
     '{"pm25": {"warning": 60, "alert": 100, "critical": 250}, "aqi": {"warning": 150, "alert": 200, "critical": 300}}'),
    ('Beijing', 'China', 39.9042, 116.4074, 'Asia/Shanghai', 21540000, true,
     '{"pm25": {"warning": 75, "alert": 150, "critical": 250}, "aqi": {"warning": 150, "alert": 200, "critical": 300}}')
ON CONFLICT (city) DO NOTHING;

-- Create aggregated hourly data table for faster dashboard queries
CREATE TABLE IF NOT EXISTS air_quality_hourly (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    hour_timestamp TIMESTAMP NOT NULL,
    avg_pm25 DECIMAL(10, 2),
    avg_pm10 DECIMAL(10, 2),
    avg_co DECIMAL(10, 2),
    avg_no2 DECIMAL(10, 2),
    avg_o3 DECIMAL(10, 2),
    avg_so2 DECIMAL(10, 2),
    avg_aqi INTEGER,
    max_aqi INTEGER,
    min_aqi INTEGER,
    measurement_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(city, hour_timestamp)
);

CREATE INDEX idx_hourly_city_timestamp ON air_quality_hourly(city, hour_timestamp DESC);