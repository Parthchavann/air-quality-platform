# Air Quality Platform - Deployment Guide

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Python 3.9+ (for local development)
- At least 8GB RAM available for containers
- API keys (optional but recommended):
  - OpenWeatherMap API key
  - IQAir API key

### 1. Clone and Setup
```bash
git clone <repository-url>
cd air-quality-platform
cp .env.example .env
```

### 2. Configure API Keys (Optional)
Edit `.env` file with your API keys:
```bash
OPENWEATHER_API_KEY=your_api_key_here
IQAIR_API_KEY=your_api_key_here
```

### 3. Start the Platform
```bash
./start_platform.sh
```

### 4. Access Services
- **Main Dashboard**: http://localhost:8501
- **Airflow**: http://localhost:8080 (admin/admin)
- **Kafka UI**: http://localhost:8082
- **Spark Master**: http://localhost:8083
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│    Kafka     │───▶│ Spark Streaming │
│  (APIs/Sensors) │    │   (Stream)   │    │   (Processing)  │
└─────────────────┘    └──────────────┘    └─────────────────┘
                                                     │
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Streamlit     │◀───│ PostgreSQL   │◀───│   Delta Lake    │
│  (Dashboard)    │    │ (Analytics)  │    │   (Storage)     │
└─────────────────┘    └──────────────┘    └─────────────────┘
                                │
                       ┌──────────────┐
                       │   Airflow    │
                       │(Orchestration)│
                       └──────────────┘
```

## 📊 Data Pipeline Flow

1. **Data Ingestion**
   - Collects data from OpenAQ, IQAir, and OpenWeatherMap APIs
   - Fallback to simulated data if APIs unavailable
   - Publishes to Kafka topics

2. **Stream Processing**
   - Spark Structured Streaming consumes from Kafka
   - Real-time data validation and transformation
   - Writes to Delta Lake and PostgreSQL

3. **Data Quality**
   - Great Expectations validates data quality
   - Anomaly detection using ML algorithms
   - Automated alerts for critical conditions

4. **Orchestration**
   - Airflow manages the entire pipeline
   - Scheduled data collection every 15 minutes
   - Health checks and automated recovery

5. **Visualization**
   - Streamlit dashboard with real-time updates
   - KeplerGL for advanced geospatial visualization
   - Grafana for system monitoring

## 🛠️ Configuration Options

### Environment Variables
```bash
# API Configuration
OPENAQ_API_KEY=your_key
OPENWEATHER_API_KEY=your_key
IQAIR_API_KEY=your_key

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_AIR_QUALITY=air-quality-stream

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_DB=airquality
POSTGRES_USER=airquality_user
POSTGRES_PASSWORD=secure_password

# Cities to Monitor
MONITORED_CITIES=New York,Los Angeles,Chicago,London,Paris,Tokyo,Delhi,Beijing
```

### Data Collection Frequency
Edit `src/orchestration/dags/air_quality_dag.py`:
```python
schedule_interval=timedelta(minutes=15)  # Change collection frequency
```

### Alert Thresholds
Modify thresholds in `docker/init-db.sql`:
```sql
INSERT INTO city_configurations (city, alert_thresholds) VALUES 
('City', '{"pm25": {"warning": 35, "alert": 55, "critical": 150}}');
```

## 🔍 Monitoring & Troubleshooting

### Health Checks
```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs streamlit
docker-compose logs airflow-webserver
docker-compose logs kafka

# Check data pipeline
curl http://localhost:8501/_stcore/health
```

### Common Issues

1. **Kafka Connection Issues**
   ```bash
   docker-compose restart kafka zookeeper
   sleep 30
   docker-compose up -d
   ```

2. **Database Connection Issues**
   ```bash
   docker-compose restart postgres
   # Wait for database to be ready
   docker-compose logs postgres | grep "ready to accept"
   ```

3. **Memory Issues**
   - Reduce Spark worker memory in `docker-compose.yml`
   - Limit data retention period
   - Run fewer containers simultaneously

4. **API Rate Limits**
   - Increase `REQUEST_DELAY` in config
   - Use fewer cities in `MONITORED_CITIES`
   - Rely on simulated data for testing

### Performance Tuning

1. **For High-Volume Data**
   ```yaml
   # In docker-compose.yml
   spark-worker:
     environment:
       - SPARK_WORKER_MEMORY=4G
       - SPARK_WORKER_CORES=4
   ```

2. **For Low-Resource Systems**
   ```yaml
   # Reduce resource allocation
   spark-worker:
     environment:
       - SPARK_WORKER_MEMORY=1G
       - SPARK_WORKER_CORES=1
   ```

3. **Database Performance**
   ```sql
   -- Add indexes for common queries
   CREATE INDEX idx_timestamp_city ON air_quality_measurements(timestamp, city);
   CREATE INDEX idx_aqi_severity ON pollution_alerts(severity, timestamp);
   ```

## 📈 Scaling Considerations

### Horizontal Scaling
1. **Multiple Kafka Brokers**
   - Add broker instances in docker-compose.yml
   - Increase replication factor

2. **Spark Cluster**
   - Add more worker nodes
   - Increase parallelism settings

3. **Database Scaling**
   - Consider PostgreSQL clustering
   - Implement read replicas

### Production Deployment
1. **Security**
   - Use secrets management (Vault, K8s secrets)
   - Enable SSL/TLS for all services
   - Set up proper authentication

2. **High Availability**
   - Deploy on Kubernetes
   - Use managed services (RDS, MSK, etc.)
   - Implement disaster recovery

3. **Monitoring**
   - Set up comprehensive logging
   - Configure alerting rules
   - Monitor resource usage

## 🧪 Testing

### Unit Tests
```bash
./run_tests.sh
```

### Integration Tests
```bash
# Test full pipeline
python src/ingestion/data_ingestion_pipeline.py --mode once
python src/processing/air_quality_processor.py
```

### Load Testing
```bash
# Generate test data
python tests/generate_test_data.py --records 1000
```

## 🚨 Production Checklist

- [ ] Configure proper authentication
- [ ] Set up SSL certificates
- [ ] Configure backup strategy
- [ ] Set up monitoring alerts
- [ ] Document operational procedures
- [ ] Train operations team
- [ ] Perform disaster recovery test
- [ ] Configure log rotation
- [ ] Set up resource monitoring
- [ ] Document scaling procedures

## 📞 Support

For issues and questions:
1. Check logs using `docker-compose logs [service]`
2. Review configuration in `.env` file
3. Ensure all services are healthy
4. Check resource availability (CPU, memory, disk)
5. Verify network connectivity to external APIs

## 🔄 Updates

To update the platform:
```bash
./stop_platform.sh
git pull origin main
./start_platform.sh
```

For major updates, backup data first:
```bash
docker-compose exec postgres pg_dump airquality > backup.sql
```