#!/usr/bin/env python3
"""
Advanced anomaly detection and alerting system for air quality data
"""

import os
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import psycopg2
from sqlalchemy import create_engine
import smtplib
import json
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders

from kafka_producer import AirQualityKafkaProducer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AirQualityAnomalyDetector:
    """Advanced anomaly detection system for air quality monitoring"""
    
    def __init__(self):
        self.postgres_url = self._get_postgres_url()
        self.engine = create_engine(self.postgres_url)
        self.kafka_producer = AirQualityKafkaProducer()
        
        # Anomaly detection parameters
        self.isolation_forest_params = {
            'contamination': 0.1,  # Expected proportion of outliers
            'random_state': 42,
            'n_estimators': 100
        }
        
        # Statistical thresholds
        self.statistical_thresholds = {
            'z_score_threshold': 3.0,
            'iqr_multiplier': 1.5,
            'rolling_window': 24,  # hours
            'min_samples': 10
        }
        
        # Pollution thresholds by pollutant (WHO and EPA standards)
        self.pollution_thresholds = {
            'pm25': {
                'good': 15,
                'moderate': 35,
                'unhealthy_sensitive': 55,
                'unhealthy': 150,
                'very_unhealthy': 250,
                'hazardous': 500
            },
            'pm10': {
                'good': 50,
                'moderate': 100,
                'unhealthy_sensitive': 150,
                'unhealthy': 200,
                'very_unhealthy': 300,
                'hazardous': 500
            },
            'no2': {
                'good': 50,
                'moderate': 100,
                'unhealthy_sensitive': 200,
                'unhealthy': 400,
                'very_unhealthy': 1000,
                'hazardous': 2000
            },
            'o3': {
                'good': 70,
                'moderate': 140,
                'unhealthy_sensitive': 180,
                'unhealthy': 240,
                'very_unhealthy': 300,
                'hazardous': 400
            },
            'co': {
                'good': 4,
                'moderate': 9,
                'unhealthy_sensitive': 15,
                'unhealthy': 30,
                'very_unhealthy': 40,
                'hazardous': 50
            },
            'so2': {
                'good': 20,
                'moderate': 80,
                'unhealthy_sensitive': 200,
                'unhealthy': 400,
                'very_unhealthy': 800,
                'hazardous': 1000
            },
            'aqi': {
                'good': 50,
                'moderate': 100,
                'unhealthy_sensitive': 150,
                'unhealthy': 200,
                'very_unhealthy': 300,
                'hazardous': 500
            }
        }
        
        # Weather-pollution correlation thresholds
        self.weather_correlation_thresholds = {
            'high_temp_pollution_correlation': 0.7,  # High temp often correlates with pollution
            'low_wind_pollution_threshold': 2.0,     # Low wind speed threshold (m/s)
            'high_humidity_threshold': 85,           # High humidity threshold (%)
            'inversion_temperature_gradient': -2.0   # Temperature inversion indicator
        }
    
    def _get_postgres_url(self) -> str:
        """Get PostgreSQL connection URL"""
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = os.getenv('POSTGRES_PORT', '5432')
        database = os.getenv('POSTGRES_DB', 'airquality')
        username = os.getenv('POSTGRES_USER', 'airquality_user')
        password = os.getenv('POSTGRES_PASSWORD', 'secure_password')
        
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    def get_recent_data(self, hours: int = 48) -> pd.DataFrame:
        """Get recent air quality and weather data"""
        query = """
        SELECT 
            aq.city,
            aq.timestamp,
            aq.pm25, aq.pm10, aq.co, aq.no2, aq.o3, aq.so2, aq.aqi,
            aq.latitude, aq.longitude,
            w.temperature, w.humidity, w.pressure, w.wind_speed, w.wind_direction,
            w.description as weather_description
        FROM air_quality_measurements aq
        LEFT JOIN weather_data w ON aq.city = w.city 
            AND ABS(EXTRACT(EPOCH FROM (aq.timestamp - w.timestamp))) < 3600
        WHERE aq.timestamp >= NOW() - INTERVAL '%s hours'
        ORDER BY aq.timestamp DESC
        """
        
        try:
            df = pd.read_sql_query(query, self.engine, params=[hours])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            logger.info(f"Retrieved {len(df)} records for anomaly detection")
            return df
        except Exception as e:
            logger.error(f"Failed to retrieve data: {e}")
            return pd.DataFrame()
    
    def detect_statistical_anomalies(self, df: pd.DataFrame, city: str = None) -> List[Dict[str, Any]]:
        """Detect anomalies using statistical methods"""
        anomalies = []
        
        # Filter by city if specified
        if city:
            df = df[df['city'] == city]
        
        if df.empty:
            return anomalies
        
        pollutants = ['pm25', 'pm10', 'co', 'no2', 'o3', 'so2', 'aqi']
        
        for city_name in df['city'].unique():
            city_data = df[df['city'] == city_name].sort_values('timestamp')
            
            if len(city_data) < self.statistical_thresholds['min_samples']:
                continue
            
            for pollutant in pollutants:
                if pollutant not in city_data.columns or city_data[pollutant].isna().all():
                    continue
                
                values = city_data[pollutant].dropna()
                if len(values) < 3:
                    continue
                
                # Z-score based anomaly detection
                z_scores = np.abs((values - values.mean()) / values.std())
                z_anomalies = values[z_scores > self.statistical_thresholds['z_score_threshold']]
                
                # IQR based anomaly detection
                Q1 = values.quantile(0.25)
                Q3 = values.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - self.statistical_thresholds['iqr_multiplier'] * IQR
                upper_bound = Q3 + self.statistical_thresholds['iqr_multiplier'] * IQR
                iqr_anomalies = values[(values < lower_bound) | (values > upper_bound)]
                
                # Rolling window anomaly detection
                if len(values) >= self.statistical_thresholds['rolling_window']:
                    rolling_mean = values.rolling(window=12, center=True).mean()
                    rolling_std = values.rolling(window=12, center=True).std()
                    rolling_anomalies = values[
                        np.abs(values - rolling_mean) > 2 * rolling_std
                    ]
                else:
                    rolling_anomalies = pd.Series()
                
                # Combine anomaly detections
                all_anomaly_indices = set(z_anomalies.index) | set(iqr_anomalies.index) | set(rolling_anomalies.index)
                
                for idx in all_anomaly_indices:
                    anomaly_record = city_data.loc[idx]
                    anomaly_value = anomaly_record[pollutant]
                    
                    # Determine severity
                    severity = self._determine_severity(pollutant, anomaly_value)
                    
                    anomaly = {
                        'type': 'statistical_anomaly',
                        'city': city_name,
                        'timestamp': anomaly_record['timestamp'],
                        'pollutant': pollutant,
                        'value': float(anomaly_value),
                        'expected_range': [float(values.quantile(0.1)), float(values.quantile(0.9))],
                        'severity': severity,
                        'detection_method': self._get_detection_methods(idx, z_anomalies, iqr_anomalies, rolling_anomalies),
                        'message': f"Statistical anomaly detected: {pollutant.upper()} level of {anomaly_value:.2f} in {city_name}",
                        'latitude': float(anomaly_record['latitude']) if pd.notna(anomaly_record['latitude']) else None,
                        'longitude': float(anomaly_record['longitude']) if pd.notna(anomaly_record['longitude']) else None
                    }
                    
                    anomalies.append(anomaly)
        
        logger.info(f"Detected {len(anomalies)} statistical anomalies")
        return anomalies
    
    def detect_ml_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies using machine learning methods"""
        anomalies = []
        
        if df.empty:
            return anomalies
        
        pollutants = ['pm25', 'pm10', 'co', 'no2', 'o3', 'so2']
        
        for city in df['city'].unique():
            city_data = df[df['city'] == city].copy()
            
            if len(city_data) < 20:  # Need minimum samples for ML
                continue
            
            # Prepare features for ML
            features = city_data[pollutants + ['temperature', 'humidity', 'pressure', 'wind_speed']].fillna(0)
            
            if features.empty or features.shape[1] == 0:
                continue
            
            # Standardize features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Isolation Forest
            iso_forest = IsolationForest(**self.isolation_forest_params)
            anomaly_labels = iso_forest.fit_predict(features_scaled)
            anomaly_scores = iso_forest.decision_function(features_scaled)
            
            # DBSCAN for clustering-based anomaly detection
            dbscan = DBSCAN(eps=0.5, min_samples=5)
            cluster_labels = dbscan.fit_predict(features_scaled)
            
            # Identify anomalies
            iso_anomalies = np.where(anomaly_labels == -1)[0]
            cluster_anomalies = np.where(cluster_labels == -1)[0]  # Noise points
            
            # Combine results
            all_ml_anomalies = set(iso_anomalies) | set(cluster_anomalies)
            
            for idx in all_ml_anomalies:
                anomaly_record = city_data.iloc[idx]
                
                # Find the most anomalous pollutant
                pollutant_values = {p: anomaly_record[p] for p in pollutants if pd.notna(anomaly_record[p])}
                if not pollutant_values:
                    continue
                
                # Use the pollutant with highest relative deviation
                city_means = city_data[pollutants].mean()
                city_stds = city_data[pollutants].std()
                
                relative_deviations = {}
                for p, val in pollutant_values.items():
                    if city_stds[p] > 0:
                        relative_deviations[p] = abs((val - city_means[p]) / city_stds[p])
                
                if relative_deviations:
                    most_anomalous_pollutant = max(relative_deviations, key=relative_deviations.get)
                    anomaly_value = pollutant_values[most_anomalous_pollutant]
                    
                    severity = self._determine_severity(most_anomalous_pollutant, anomaly_value)
                    
                    anomaly = {
                        'type': 'ml_anomaly',
                        'city': city,
                        'timestamp': anomaly_record['timestamp'],
                        'pollutant': most_anomalous_pollutant,
                        'value': float(anomaly_value),
                        'anomaly_score': float(anomaly_scores[idx]) if idx < len(anomaly_scores) else None,
                        'severity': severity,
                        'detection_method': ['isolation_forest'] if idx in iso_anomalies else [] + 
                                          ['dbscan_clustering'] if idx in cluster_anomalies else [],
                        'message': f"ML-detected anomaly: {most_anomalous_pollutant.upper()} level of {anomaly_value:.2f} in {city}",
                        'latitude': float(anomaly_record['latitude']) if pd.notna(anomaly_record['latitude']) else None,
                        'longitude': float(anomaly_record['longitude']) if pd.notna(anomaly_record['longitude']) else None
                    }
                    
                    anomalies.append(anomaly)
        
        logger.info(f"Detected {len(anomalies)} ML-based anomalies")
        return anomalies
    
    def detect_weather_correlation_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies based on weather-pollution correlations"""
        anomalies = []
        
        if df.empty or 'temperature' not in df.columns:
            return anomalies
        
        for city in df['city'].unique():
            city_data = df[df['city'] == city].copy()
            
            if len(city_data) < 10:
                continue
            
            # Check for stagnant air conditions (low wind, high pollution)
            stagnant_conditions = city_data[
                (city_data['wind_speed'] <= self.weather_correlation_thresholds['low_wind_pollution_threshold']) &
                (city_data['pm25'] > self.pollution_thresholds['pm25']['moderate'])
            ]
            
            for _, record in stagnant_conditions.iterrows():
                anomaly = {
                    'type': 'weather_correlation_anomaly',
                    'subtype': 'stagnant_air',
                    'city': city,
                    'timestamp': record['timestamp'],
                    'pollutant': 'pm25',
                    'value': float(record['pm25']),
                    'weather_factor': f"Low wind speed: {record['wind_speed']:.1f} m/s",
                    'severity': 'warning' if record['pm25'] < self.pollution_thresholds['pm25']['unhealthy_sensitive'] else 'alert',
                    'message': f"High pollution during stagnant air conditions in {city}: PM2.5 {record['pm25']:.1f} µg/m³, Wind {record['wind_speed']:.1f} m/s",
                    'latitude': float(record['latitude']) if pd.notna(record['latitude']) else None,
                    'longitude': float(record['longitude']) if pd.notna(record['longitude']) else None
                }
                anomalies.append(anomaly)
            
            # Check for high humidity + pollution (often indicates poor air quality conditions)
            high_humidity_pollution = city_data[
                (city_data['humidity'] >= self.weather_correlation_thresholds['high_humidity_threshold']) &
                (city_data['pm25'] > self.pollution_thresholds['pm25']['moderate'])
            ]
            
            for _, record in high_humidity_pollution.iterrows():
                anomaly = {
                    'type': 'weather_correlation_anomaly',
                    'subtype': 'high_humidity_pollution',
                    'city': city,
                    'timestamp': record['timestamp'],
                    'pollutant': 'pm25',
                    'value': float(record['pm25']),
                    'weather_factor': f"High humidity: {record['humidity']:.1f}%",
                    'severity': 'warning',
                    'message': f"High pollution with high humidity in {city}: PM2.5 {record['pm25']:.1f} µg/m³, Humidity {record['humidity']:.1f}%",
                    'latitude': float(record['latitude']) if pd.notna(record['latitude']) else None,
                    'longitude': float(record['longitude']) if pd.notna(record['longitude']) else None
                }
                anomalies.append(anomaly)
        
        logger.info(f"Detected {len(anomalies)} weather-correlation anomalies")
        return anomalies
    
    def detect_threshold_violations(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect threshold violations for immediate alerts"""
        violations = []
        
        if df.empty:
            return violations
        
        # Get the most recent data for each city
        latest_data = df.groupby('city').last().reset_index()
        
        for _, record in latest_data.iterrows():
            city = record['city']
            
            for pollutant, thresholds in self.pollution_thresholds.items():
                if pollutant not in record or pd.isna(record[pollutant]):
                    continue
                
                value = record[pollutant]
                
                # Determine violation level
                violation_level = None
                threshold_exceeded = None
                
                if value >= thresholds['hazardous']:
                    violation_level = 'critical'
                    threshold_exceeded = thresholds['hazardous']
                elif value >= thresholds['very_unhealthy']:
                    violation_level = 'alert'
                    threshold_exceeded = thresholds['very_unhealthy']
                elif value >= thresholds['unhealthy']:
                    violation_level = 'alert'
                    threshold_exceeded = thresholds['unhealthy']
                elif value >= thresholds['unhealthy_sensitive']:
                    violation_level = 'warning'
                    threshold_exceeded = thresholds['unhealthy_sensitive']
                
                if violation_level:
                    violation = {
                        'type': 'threshold_violation',
                        'city': city,
                        'timestamp': record['timestamp'],
                        'pollutant': pollutant,
                        'value': float(value),
                        'threshold': float(threshold_exceeded),
                        'severity': violation_level,
                        'message': f"{pollutant.upper()} level exceeds {violation_level} threshold in {city}: {value:.2f} (threshold: {threshold_exceeded})",
                        'health_impact': self._get_health_impact(pollutant, violation_level),
                        'recommendations': self._get_recommendations(pollutant, violation_level),
                        'latitude': float(record['latitude']) if pd.notna(record['latitude']) else None,
                        'longitude': float(record['longitude']) if pd.notna(record['longitude']) else None
                    }
                    violations.append(violation)
        
        logger.info(f"Detected {len(violations)} threshold violations")
        return violations
    
    def _determine_severity(self, pollutant: str, value: float) -> str:
        """Determine severity level based on pollutant and value"""
        if pollutant not in self.pollution_thresholds:
            return 'warning'
        
        thresholds = self.pollution_thresholds[pollutant]
        
        if value >= thresholds['hazardous']:
            return 'critical'
        elif value >= thresholds['very_unhealthy']:
            return 'alert'
        elif value >= thresholds['unhealthy']:
            return 'alert'
        elif value >= thresholds['unhealthy_sensitive']:
            return 'warning'
        else:
            return 'info'
    
    def _get_detection_methods(self, idx, z_anomalies, iqr_anomalies, rolling_anomalies) -> List[str]:
        """Get list of detection methods that identified the anomaly"""
        methods = []
        if idx in z_anomalies.index:
            methods.append('z_score')
        if idx in iqr_anomalies.index:
            methods.append('iqr')
        if idx in rolling_anomalies.index:
            methods.append('rolling_window')
        return methods
    
    def _get_health_impact(self, pollutant: str, severity: str) -> str:
        """Get health impact description"""
        impact_map = {
            'pm25': {
                'warning': 'May cause respiratory irritation in sensitive individuals',
                'alert': 'May cause health effects in all individuals, especially sensitive groups',
                'critical': 'Emergency conditions - serious health effects for entire population'
            },
            'pm10': {
                'warning': 'May affect sensitive individuals with respiratory conditions',
                'alert': 'May cause breathing difficulties and throat irritation',
                'critical': 'Serious risk to cardiovascular and respiratory health'
            },
            'no2': {
                'warning': 'May trigger asthma symptoms in sensitive individuals',
                'alert': 'Respiratory irritation and reduced lung function',
                'critical': 'Severe respiratory distress and potential lung damage'
            },
            'o3': {
                'warning': 'May cause chest tightness and coughing',
                'alert': 'Breathing difficulties and reduced lung function',
                'critical': 'Severe respiratory symptoms and potential long-term damage'
            }
        }
        
        return impact_map.get(pollutant, {}).get(severity, 'Health effects possible')
    
    def _get_recommendations(self, pollutant: str, severity: str) -> List[str]:
        """Get health recommendations"""
        if severity == 'critical':
            return [
                "Stay indoors with windows and doors closed",
                "Avoid all outdoor activities",
                "Use air purifiers if available",
                "Seek medical attention if experiencing symptoms",
                "Consider evacuation if conditions persist"
            ]
        elif severity == 'alert':
            return [
                "Limit outdoor activities, especially strenuous exercise",
                "Sensitive individuals should stay indoors",
                "Wear N95 masks if going outside",
                "Keep windows closed and use air conditioning",
                "Monitor air quality forecasts"
            ]
        else:
            return [
                "Sensitive individuals should limit prolonged outdoor exertion",
                "Consider reducing outdoor activities",
                "Monitor symptoms and air quality updates"
            ]
    
    def run_anomaly_detection(self, hours: int = 24) -> Dict[str, Any]:
        """Run complete anomaly detection suite"""
        logger.info(f"Starting anomaly detection for last {hours} hours")
        
        # Get data
        df = self.get_recent_data(hours)
        
        if df.empty:
            logger.warning("No data available for anomaly detection")
            return {'anomalies': [], 'summary': {'total': 0}}
        
        # Run different detection methods
        statistical_anomalies = self.detect_statistical_anomalies(df)
        ml_anomalies = self.detect_ml_anomalies(df)
        weather_anomalies = self.detect_weather_correlation_anomalies(df)
        threshold_violations = self.detect_threshold_violations(df)
        
        # Combine all anomalies
        all_anomalies = (
            statistical_anomalies + 
            ml_anomalies + 
            weather_anomalies + 
            threshold_violations
        )
        
        # Remove duplicates and prioritize by severity
        unique_anomalies = self._deduplicate_anomalies(all_anomalies)
        
        # Create summary
        summary = {
            'total': len(unique_anomalies),
            'by_type': self._summarize_by_type(unique_anomalies),
            'by_severity': self._summarize_by_severity(unique_anomalies),
            'by_city': self._summarize_by_city(unique_anomalies),
            'timestamp': datetime.now()
        }
        
        # Send alerts for critical anomalies
        critical_anomalies = [a for a in unique_anomalies if a.get('severity') == 'critical']
        if critical_anomalies:
            self._send_critical_alerts(critical_anomalies)
        
        logger.info(f"Anomaly detection completed: {summary['total']} anomalies found")
        
        return {
            'anomalies': unique_anomalies,
            'summary': summary
        }
    
    def _deduplicate_anomalies(self, anomalies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate anomalies and keep the most severe ones"""
        # Group by city, pollutant, and time window
        grouped = {}
        
        for anomaly in anomalies:
            key = (
                anomaly['city'],
                anomaly['pollutant'],
                anomaly['timestamp'].replace(minute=0, second=0, microsecond=0)  # Group by hour
            )
            
            if key not in grouped or self._get_severity_weight(anomaly['severity']) > self._get_severity_weight(grouped[key]['severity']):
                grouped[key] = anomaly
        
        return list(grouped.values())
    
    def _get_severity_weight(self, severity: str) -> int:
        """Get numeric weight for severity"""
        weights = {'info': 1, 'warning': 2, 'alert': 3, 'critical': 4}
        return weights.get(severity, 1)
    
    def _summarize_by_type(self, anomalies: List[Dict[str, Any]]) -> Dict[str, int]:
        """Summarize anomalies by detection type"""
        type_counts = {}
        for anomaly in anomalies:
            anomaly_type = anomaly['type']
            type_counts[anomaly_type] = type_counts.get(anomaly_type, 0) + 1
        return type_counts
    
    def _summarize_by_severity(self, anomalies: List[Dict[str, Any]]) -> Dict[str, int]:
        """Summarize anomalies by severity"""
        severity_counts = {}
        for anomaly in anomalies:
            severity = anomaly['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        return severity_counts
    
    def _summarize_by_city(self, anomalies: List[Dict[str, Any]]) -> Dict[str, int]:
        """Summarize anomalies by city"""
        city_counts = {}
        for anomaly in anomalies:
            city = anomaly['city']
            city_counts[city] = city_counts.get(city, 0) + 1
        return city_counts
    
    def _send_critical_alerts(self, critical_anomalies: List[Dict[str, Any]]):
        """Send alerts for critical anomalies"""
        try:
            # Send to Kafka for real-time processing
            for anomaly in critical_anomalies:
                alert_data = {
                    'city': anomaly['city'],
                    'alert_type': 'critical_anomaly',
                    'severity': 'critical',
                    'pollutant': anomaly['pollutant'],
                    'value': anomaly['value'],
                    'threshold': anomaly.get('threshold', 0),
                    'message': anomaly['message'],
                    'timestamp': anomaly['timestamp'].isoformat(),
                    'acknowledged': False,
                    'anomaly_type': anomaly['type'],
                    'health_impact': anomaly.get('health_impact', ''),
                    'recommendations': anomaly.get('recommendations', [])
                }
                
                self.kafka_producer.send_alert(alert_data)
            
            # Send email notification
            self._send_email_notification(critical_anomalies)
            
            logger.info(f"Sent alerts for {len(critical_anomalies)} critical anomalies")
            
        except Exception as e:
            logger.error(f"Failed to send critical alerts: {e}")
    
    def _send_email_notification(self, anomalies: List[Dict[str, Any]]):
        """Send email notification for critical anomalies"""
        # Email configuration
        smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')
        alert_email_to = os.getenv('ALERT_EMAIL_TO')
        
        if not all([smtp_user, smtp_password, alert_email_to]):
            logger.warning("Email configuration incomplete, skipping email notification")
            return
        
        # Create email content
        subject = f"🚨 CRITICAL Air Quality Anomalies Detected - {len(anomalies)} Alerts"
        
        body = f"Critical air quality anomalies have been detected at {datetime.now()}:\n\n"
        
        for i, anomaly in enumerate(anomalies, 1):
            body += f"{i}. {anomaly['city']} - {anomaly['pollutant'].upper()}\n"
            body += f"   Value: {anomaly['value']:.2f}\n"
            body += f"   Type: {anomaly['type']}\n"
            body += f"   Message: {anomaly['message']}\n"
            if 'health_impact' in anomaly:
                body += f"   Health Impact: {anomaly['health_impact']}\n"
            body += f"   Time: {anomaly['timestamp']}\n\n"
        
        body += "Please check the dashboard for more details and take appropriate action.\n"
        body += f"Dashboard: http://localhost:8501\n"
        
        # Send email
        try:
            msg = MimeMultipart()
            msg['From'] = smtp_user
            msg['To'] = alert_email_to
            msg['Subject'] = subject
            msg.attach(MimeText(body, 'plain'))
            
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            logger.info("Critical anomaly email notification sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")

def main():
    """Main function for standalone execution"""
    detector = AirQualityAnomalyDetector()
    
    # Run anomaly detection
    results = detector.run_anomaly_detection(hours=24)
    
    print("\n=== Anomaly Detection Results ===")
    print(f"Total anomalies detected: {results['summary']['total']}")
    
    print("\nBy Type:")
    for anomaly_type, count in results['summary']['by_type'].items():
        print(f"  {anomaly_type}: {count}")
    
    print("\nBy Severity:")
    for severity, count in results['summary']['by_severity'].items():
        print(f"  {severity}: {count}")
    
    print("\nBy City:")
    for city, count in results['summary']['by_city'].items():
        print(f"  {city}: {count}")
    
    print("\n=== Critical Anomalies ===")
    critical = [a for a in results['anomalies'] if a.get('severity') == 'critical']
    for anomaly in critical:
        print(f"• {anomaly['city']}: {anomaly['message']}")

if __name__ == "__main__":
    main()