#!/usr/bin/env python3
"""
Airflow DAG for Air Quality Data Pipeline Orchestration
"""

from datetime import datetime, timedelta
from typing import Any, Dict
import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.sensors.filesystem import FileSensor
from airflow.utils.task_group import TaskGroup
from airflow.utils.dates import days_ago
from airflow.models import Variable

# Default arguments for the DAG
default_args = {
    'owner': 'airquality-team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'catchup': False,
}

# DAG definition
dag = DAG(
    'air_quality_pipeline',
    default_args=default_args,
    description='End-to-end air quality data pipeline',
    schedule_interval=timedelta(minutes=15),  # Run every 15 minutes
    max_active_runs=1,
    tags=['air_quality', 'data_pipeline', 'monitoring'],
    doc_md="""
    ## Air Quality Data Pipeline DAG
    
    This DAG orchestrates the complete air quality monitoring pipeline:
    
    1. **Data Ingestion**: Collect data from multiple APIs
    2. **Data Processing**: Stream processing with Spark
    3. **Data Quality**: Validate data quality with Great Expectations
    4. **Alerting**: Generate and send pollution alerts
    5. **Monitoring**: Check system health and data freshness
    
    ### Schedule
    - Runs every 15 minutes
    - Includes data quality checks
    - Automated alerting for critical conditions
    
    ### Dependencies
    - Kafka cluster must be running
    - Spark cluster must be available
    - PostgreSQL database must be accessible
    """,
)

def check_system_health(**context) -> Dict[str, Any]:
    """Check system health and dependencies"""
    import requests
    import psycopg2
    from kafka import KafkaProducer
    import os
    
    health_status = {
        'timestamp': datetime.now(),
        'kafka': False,
        'postgres': False,
        'spark': False,
        'apis': []
    }
    
    # Check Kafka
    try:
        producer = KafkaProducer(
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            request_timeout_ms=5000
        )
        producer.close()
        health_status['kafka'] = True
        logging.info("Kafka health check: PASSED")
    except Exception as e:
        logging.error(f"Kafka health check: FAILED - {e}")
    
    # Check PostgreSQL
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            database=os.getenv('POSTGRES_DB', 'airquality'),
            user=os.getenv('POSTGRES_USER', 'airquality_user'),
            password=os.getenv('POSTGRES_PASSWORD', 'secure_password')
        )
        conn.close()
        health_status['postgres'] = True
        logging.info("PostgreSQL health check: PASSED")
    except Exception as e:
        logging.error(f"PostgreSQL health check: FAILED - {e}")
    
    # Check Spark (if accessible via REST API)
    try:
        spark_master_url = os.getenv('SPARK_MASTER_URL', 'http://localhost:8083')
        response = requests.get(f"{spark_master_url}/", timeout=10)
        if response.status_code == 200:
            health_status['spark'] = True
            logging.info("Spark health check: PASSED")
    except Exception as e:
        logging.error(f"Spark health check: FAILED - {e}")
    
    # Check external APIs
    api_endpoints = [
        ('OpenAQ', 'https://api.openaq.org/v2/latest?limit=1'),
        ('OpenWeather', f"https://api.openweathermap.org/data/2.5/weather?q=London&appid={os.getenv('OPENWEATHER_API_KEY', 'test')}")
    ]
    
    for api_name, url in api_endpoints:
        try:
            response = requests.get(url, timeout=10)
            api_status = {
                'name': api_name,
                'status': response.status_code == 200,
                'response_time': response.elapsed.total_seconds()
            }
            health_status['apis'].append(api_status)
            logging.info(f"{api_name} API health check: {'PASSED' if api_status['status'] else 'FAILED'}")
        except Exception as e:
            health_status['apis'].append({
                'name': api_name,
                'status': False,
                'error': str(e)
            })
            logging.error(f"{api_name} API health check: FAILED - {e}")
    
    # Store health status for downstream tasks
    context['task_instance'].xcom_push(key='health_status', value=health_status)
    
    # Raise exception if critical systems are down
    if not health_status['kafka'] or not health_status['postgres']:
        raise Exception("Critical systems (Kafka or PostgreSQL) are not available")
    
    return health_status

def run_data_ingestion(**context) -> Dict[str, Any]:
    """Run data ingestion pipeline"""
    import subprocess
    import os
    
    # Change to ingestion directory
    ingestion_dir = "/opt/airflow/dags/src/ingestion"
    
    # Run data ingestion pipeline
    cmd = [
        "python", 
        f"{ingestion_dir}/data_ingestion_pipeline.py",
        "--mode", "once"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=ingestion_dir
        )
        
        if result.returncode == 0:
            logging.info("Data ingestion completed successfully")
            logging.info(f"Output: {result.stdout}")
            
            return {
                'status': 'success',
                'message': 'Data ingestion completed',
                'records_processed': 'check logs'  # This could be parsed from output
            }
        else:
            logging.error(f"Data ingestion failed: {result.stderr}")
            raise Exception(f"Data ingestion failed with code {result.returncode}")
            
    except subprocess.TimeoutExpired:
        logging.error("Data ingestion timed out")
        raise Exception("Data ingestion process timed out")
    except Exception as e:
        logging.error(f"Data ingestion error: {e}")
        raise

def validate_data_quality(**context) -> Dict[str, Any]:
    """Validate data quality using Great Expectations"""
    import pandas as pd
    import psycopg2
    import os
    from datetime import datetime, timedelta
    
    # Connect to database
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        database=os.getenv('POSTGRES_DB', 'airquality'),
        user=os.getenv('POSTGRES_USER', 'airquality_user'),
        password=os.getenv('POSTGRES_PASSWORD', 'secure_password')
    )
    
    # Get recent data for validation
    query = """
    SELECT city, pm25, pm10, aqi, timestamp, source
    FROM air_quality_measurements 
    WHERE timestamp >= NOW() - INTERVAL '1 hour'
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Simple data quality checks
    quality_issues = []
    
    # Check for missing data
    if df.empty:
        quality_issues.append("No recent data found")
    
    # Check for null values in critical columns
    critical_columns = ['city', 'pm25', 'aqi']
    for col in critical_columns:
        null_count = df[col].isnull().sum()
        null_percentage = (null_count / len(df)) * 100 if len(df) > 0 else 0
        
        if null_percentage > 20:  # More than 20% null values
            quality_issues.append(f"High null percentage in {col}: {null_percentage:.1f}%")
    
    # Check for outliers (basic check)
    if not df.empty:
        # PM2.5 should be between 0 and 500
        pm25_outliers = df[(df['pm25'] < 0) | (df['pm25'] > 500)]
        if not pm25_outliers.empty:
            quality_issues.append(f"PM2.5 outliers detected: {len(pm25_outliers)} records")
        
        # AQI should be between 0 and 500
        aqi_outliers = df[(df['aqi'] < 0) | (df['aqi'] > 500)]
        if not aqi_outliers.empty:
            quality_issues.append(f"AQI outliers detected: {len(aqi_outliers)} records")
    
    # Check data freshness
    if not df.empty:
        latest_timestamp = pd.to_datetime(df['timestamp']).max()
        time_diff = datetime.now() - latest_timestamp.tz_localize(None) if latest_timestamp.tz else datetime.now() - latest_timestamp
        
        if time_diff > timedelta(minutes=30):
            quality_issues.append(f"Data is stale: latest record is {time_diff} old")
    
    quality_result = {
        'timestamp': datetime.now(),
        'records_checked': len(df),
        'issues_found': len(quality_issues),
        'issues': quality_issues,
        'passed': len(quality_issues) == 0
    }
    
    # Store result for downstream tasks
    context['task_instance'].xcom_push(key='quality_result', value=quality_result)
    
    if not quality_result['passed']:
        logging.warning(f"Data quality issues found: {quality_issues}")
        # Don't fail the task for quality issues, just log them
    
    return quality_result

def check_pollution_alerts(**context) -> Dict[str, Any]:
    """Check for active pollution alerts and send notifications"""
    import psycopg2
    import os
    import smtplib
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    
    # Connect to database
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        database=os.getenv('POSTGRES_DB', 'airquality'),
        user=os.getenv('POSTGRES_USER', 'airquality_user'),
        password=os.getenv('POSTGRES_PASSWORD', 'secure_password')
    )
    
    # Get unacknowledged alerts
    cursor = conn.cursor()
    cursor.execute("""
        SELECT city, severity, pollutant, value, threshold, message, timestamp
        FROM pollution_alerts 
        WHERE acknowledged = false 
        AND timestamp >= NOW() - INTERVAL '1 hour'
        ORDER BY severity DESC, timestamp DESC
    """)
    
    alerts = cursor.fetchall()
    conn.close()
    
    alert_summary = {
        'timestamp': datetime.now(),
        'total_alerts': len(alerts),
        'critical_alerts': 0,
        'high_alerts': 0,
        'warning_alerts': 0
    }
    
    if alerts:
        # Count alerts by severity
        for alert in alerts:
            severity = alert[1]
            if severity == 'critical':
                alert_summary['critical_alerts'] += 1
            elif severity == 'alert':
                alert_summary['high_alerts'] += 1
            else:
                alert_summary['warning_alerts'] += 1
        
        # Send email notification for critical alerts
        critical_alerts = [a for a in alerts if a[1] == 'critical']
        if critical_alerts:
            try:
                send_alert_email(critical_alerts)
                logging.info(f"Alert email sent for {len(critical_alerts)} critical alerts")
            except Exception as e:
                logging.error(f"Failed to send alert email: {e}")
    
    context['task_instance'].xcom_push(key='alert_summary', value=alert_summary)
    return alert_summary

def send_alert_email(alerts):
    """Send email notification for critical alerts"""
    import smtplib
    import os
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    
    # Email configuration (should be in Airflow Variables or environment)
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    alert_email_to = os.getenv('ALERT_EMAIL_TO')
    
    if not all([smtp_user, smtp_password, alert_email_to]):
        logging.warning("Email configuration not complete, skipping email notification")
        return
    
    # Create email content
    subject = f"🚨 Critical Air Quality Alerts - {len(alerts)} Active"
    
    body = "Critical air quality alerts have been detected:\n\n"
    for alert in alerts:
        city, severity, pollutant, value, threshold, message, timestamp = alert
        body += f"• {city}: {pollutant.upper()} = {value} (threshold: {threshold}) - {message}\n"
    
    body += f"\nTimestamp: {datetime.now()}\n"
    body += "Please check the dashboard for more details."
    
    # Send email
    msg = MimeMultipart()
    msg['From'] = smtp_user
    msg['To'] = alert_email_to
    msg['Subject'] = subject
    msg.attach(MimeText(body, 'plain'))
    
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)

def cleanup_old_data(**context) -> Dict[str, Any]:
    """Clean up old data to manage storage"""
    import psycopg2
    import os
    
    # Connect to database
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        database=os.getenv('POSTGRES_DB', 'airquality'),
        user=os.getenv('POSTGRES_USER', 'airquality_user'),
        password=os.getenv('POSTGRES_PASSWORD', 'secure_password')
    )
    
    cursor = conn.cursor()
    
    cleanup_stats = {}
    
    # Clean up old air quality measurements (keep 30 days)
    cursor.execute("""
        DELETE FROM air_quality_measurements 
        WHERE timestamp < NOW() - INTERVAL '30 days'
    """)
    cleanup_stats['old_air_quality_deleted'] = cursor.rowcount
    
    # Clean up old weather data (keep 30 days)
    cursor.execute("""
        DELETE FROM weather_data 
        WHERE timestamp < NOW() - INTERVAL '30 days'
    """)
    cleanup_stats['old_weather_deleted'] = cursor.rowcount
    
    # Clean up acknowledged alerts (keep 7 days)
    cursor.execute("""
        DELETE FROM pollution_alerts 
        WHERE acknowledged = true 
        AND timestamp < NOW() - INTERVAL '7 days'
    """)
    cleanup_stats['old_alerts_deleted'] = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    cleanup_stats['timestamp'] = datetime.now()
    
    logging.info(f"Cleanup completed: {cleanup_stats}")
    return cleanup_stats

# Task definitions
start_task = DummyOperator(
    task_id='start_pipeline',
    dag=dag
)

health_check_task = PythonOperator(
    task_id='check_system_health',
    python_callable=check_system_health,
    dag=dag,
    doc_md="Check health of all system dependencies including Kafka, PostgreSQL, Spark, and external APIs"
)

# Data ingestion task group
with TaskGroup('data_ingestion_group', dag=dag) as ingestion_group:
    
    ingest_data_task = PythonOperator(
        task_id='run_data_ingestion',
        python_callable=run_data_ingestion,
        dag=dag,
        doc_md="Execute data ingestion pipeline to collect air quality and weather data"
    )
    
    validate_ingestion_task = PythonOperator(
        task_id='validate_data_quality',
        python_callable=validate_data_quality,
        dag=dag,
        doc_md="Validate quality of ingested data using Great Expectations"
    )
    
    ingest_data_task >> validate_ingestion_task

# Monitoring and alerting task group
with TaskGroup('monitoring_group', dag=dag) as monitoring_group:
    
    alert_check_task = PythonOperator(
        task_id='check_pollution_alerts',
        python_callable=check_pollution_alerts,
        dag=dag,
        doc_md="Check for active pollution alerts and send notifications"
    )
    
    cleanup_task = PythonOperator(
        task_id='cleanup_old_data',
        python_callable=cleanup_old_data,
        dag=dag,
        doc_md="Clean up old data to manage storage usage"
    )

end_task = DummyOperator(
    task_id='end_pipeline',
    dag=dag
)

# Define task dependencies
start_task >> health_check_task >> ingestion_group >> monitoring_group >> end_task

# Set up alerts for task failures
dag.doc_md = __doc__