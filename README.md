# Real-Time City Air Quality & Pollution Insights Platform

A comprehensive data engineering platform for monitoring, analyzing, and visualizing real-time air quality data across multiple cities.

## Features

- Real-time air quality data ingestion from multiple sources
- Streaming data processing with Apache Spark
- Data quality validation with Great Expectations
- Interactive dashboards with Streamlit and KeplerGL
- Anomaly detection and alerting system
- Weather data integration for enhanced insights
- Scalable architecture using Docker containers

## Architecture

```
Data Sources → Kafka → Spark Streaming → Delta Lake
                ↓                           ↓
          Airflow Orchestration      Streamlit Dashboard
                ↓                           ↓
          Data Quality Checks         KeplerGL Maps
```

## Tech Stack

- **Data Ingestion**: Python, Kafka
- **Processing**: Apache Spark Structured Streaming
- **Storage**: Delta Lake, PostgreSQL
- **Quality & Lineage**: Great Expectations, OpenLineage
- **Orchestration**: Apache Airflow
- **Visualization**: Streamlit, KeplerGL
- **Infrastructure**: Docker, Docker Compose

## Quick Start

1. Clone the repository
2. Set up environment variables: `cp .env.example .env`
3. Start the infrastructure: `docker-compose up -d`
4. Access the dashboard: http://localhost:8501
5. Access Airflow: http://localhost:8080

## Project Structure

```
air-quality-platform/
├── src/
│   ├── ingestion/       # Data ingestion scripts
│   ├── processing/      # Spark streaming jobs
│   ├── quality/         # Data quality checks
│   ├── visualization/   # Dashboard and visualizations
│   └── orchestration/   # Airflow DAGs
├── data/
│   ├── raw/            # Raw data storage
│   ├── processed/      # Processed data
│   └── delta/          # Delta Lake tables
├── config/             # Configuration files
├── docker/             # Docker configurations
├── tests/              # Test files
└── notebooks/          # Jupyter notebooks for analysis
```