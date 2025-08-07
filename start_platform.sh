#!/bin/bash

# Air Quality Monitoring Platform Startup Script

set -e

echo "🌍 Starting Air Quality Monitoring Platform..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "❌ docker-compose is not installed. Please install docker-compose and try again."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data/{raw,processed,delta}
mkdir -p logs
mkdir -p /tmp/spark-checkpoints
mkdir -p /tmp/great_expectations/{expectations,validations}

# Set environment file
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "✏️  Please edit .env file with your API keys and configuration before proceeding."
    echo "📋 Required API keys:"
    echo "   - OPENWEATHER_API_KEY: Get from https://openweathermap.org/api"
    echo "   - IQAIR_API_KEY: Get from https://www.iqair.com/air-pollution-data-api"
    echo ""
    read -p "Press Enter when you've configured the .env file..."
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

echo "🐳 Starting Docker containers..."

# Start infrastructure services first
echo "   Starting core infrastructure..."
docker-compose up -d postgres zookeeper kafka

# Wait for Kafka to be ready
echo "   Waiting for Kafka to be ready..."
sleep 30

# Start remaining services
echo "   Starting processing and monitoring services..."
docker-compose up -d spark-master spark-worker prometheus grafana

# Wait for services to initialize
echo "   Waiting for services to initialize..."
sleep 20

# Start application services
echo "   Starting application services..."
docker-compose up -d streamlit airflow-webserver airflow-scheduler airflow-init

# Wait for everything to be ready
echo "   Final initialization..."
sleep 30

# Check service status
echo ""
echo "🔍 Checking service status..."
echo "==============================="

services=("postgres" "kafka" "spark-master" "streamlit" "airflow-webserver" "prometheus" "grafana")

for service in "${services[@]}"; do
    if docker-compose ps $service | grep -q "Up"; then
        echo "✅ $service: Running"
    else
        echo "❌ $service: Not running"
    fi
done

echo ""
echo "🌐 Service URLs:"
echo "================================="
echo "📊 Main Dashboard:          http://localhost:8501"
echo "🚁 Airflow:                 http://localhost:8080 (admin/admin)"
echo "⚡ Spark Master:            http://localhost:8083"
echo "📈 Prometheus:              http://localhost:9090"
echo "📊 Grafana:                 http://localhost:3000 (admin/admin)"
echo "🎛️  Kafka UI:               http://localhost:8082"
echo ""

# Initialize Kafka topics
echo "📡 Initializing Kafka topics..."
docker-compose exec -T kafka kafka-topics --create --if-not-exists --topic air-quality-stream --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
docker-compose exec -T kafka kafka-topics --create --if-not-exists --topic weather-stream --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
docker-compose exec -T kafka kafka-topics --create --if-not-exists --topic pollution-alerts --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

echo "✅ Kafka topics created successfully"

# Start data ingestion (optional)
read -p "🔄 Start data ingestion now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Starting data ingestion pipeline..."
    python src/ingestion/data_ingestion_pipeline.py --mode continuous &
    INGESTION_PID=$!
    echo "   Data ingestion started with PID: $INGESTION_PID"
    echo "   To stop: kill $INGESTION_PID"
fi

echo ""
echo "🎉 Air Quality Monitoring Platform started successfully!"
echo ""
echo "📋 Quick Start Guide:"
echo "1. Visit the main dashboard: http://localhost:8501"
echo "2. Configure API keys in Airflow (if not already done)"
echo "3. Enable DAGs in Airflow: http://localhost:8080"
echo "4. Monitor system health in Grafana: http://localhost:3000"
echo ""
echo "🛑 To stop the platform: ./stop_platform.sh"
echo "📚 For more information, see README.md"