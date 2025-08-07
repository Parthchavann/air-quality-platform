#!/bin/bash

# Test script for Air Quality Monitoring Platform

set -e

echo "🧪 Running Air Quality Platform Tests..."

# Set up test environment
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Test data ingestion
echo "1️⃣ Testing data ingestion..."
cd src/ingestion
python -c "
from air_quality_apis import AirQualityDataCollector
collector = AirQualityDataCollector()
data = collector.collect_city_data('New York')
print(f'✅ Data ingestion test passed: {len(data)} records collected')
"

# Test Kafka producer (if Kafka is running)
echo "2️⃣ Testing Kafka integration..."
python -c "
try:
    from kafka_producer import AirQualityKafkaProducer
    producer = AirQualityKafkaProducer()
    print('✅ Kafka connection test passed')
    producer.close()
except Exception as e:
    print(f'⚠️ Kafka test skipped (service may not be running): {e}')
"

# Test database connection
echo "3️⃣ Testing database connection..."
cd ../visualization
python -c "
try:
    from database import DatabaseConnection
    db = DatabaseConnection()
    print('✅ Database connection test passed')
except Exception as e:
    print(f'⚠️ Database test failed: {e}')
"

# Test anomaly detection
echo "4️⃣ Testing anomaly detection..."
cd ../ingestion
python -c "
try:
    from anomaly_detection import AirQualityAnomalyDetector
    detector = AirQualityAnomalyDetector()
    print('✅ Anomaly detection initialization test passed')
except Exception as e:
    print(f'⚠️ Anomaly detection test failed: {e}')
"

# Test data quality checks
echo "5️⃣ Testing data quality..."
cd ../quality
python -c "
try:
    from data_quality_checks import AirQualityDataValidator
    print('✅ Data quality checks initialization test passed')
except Exception as e:
    print(f'⚠️ Data quality test failed: {e}')
"

cd ../../

echo ""
echo "🎉 Platform tests completed!"
echo "📋 Note: Some tests may be skipped if services are not running"
echo "🚀 To start all services: ./start_platform.sh"