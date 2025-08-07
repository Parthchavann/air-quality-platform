import os
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SparkConfig:
    """Configuration for Spark Structured Streaming"""
    
    # Environment variables
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    SPARK_MASTER = os.getenv('SPARK_MASTER', 'local[*]')
    SPARK_APP_NAME = os.getenv('SPARK_APP_NAME', 'AirQualityProcessor')
    CHECKPOINT_DIR = os.getenv('SPARK_CHECKPOINT_DIR', '/tmp/spark-checkpoints')
    DELTA_LAKE_PATH = os.getenv('DELTA_LAKE_PATH', '/data/delta')
    
    # Database configuration
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'airquality')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'airquality_user')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'secure_password')
    
    # Kafka topics
    KAFKA_TOPIC_AIR_QUALITY = os.getenv('KAFKA_TOPIC_AIR_QUALITY', 'air-quality-stream')
    KAFKA_TOPIC_WEATHER = os.getenv('KAFKA_TOPIC_WEATHER', 'weather-stream')
    KAFKA_TOPIC_ALERTS = os.getenv('KAFKA_TOPIC_ALERTS', 'pollution-alerts')
    
    @property
    def postgres_url(self) -> str:
        return f"jdbc:postgresql://{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def postgres_properties(self) -> dict:
        return {
            "user": self.POSTGRES_USER,
            "password": self.POSTGRES_PASSWORD,
            "driver": "org.postgresql.Driver"
        }

def create_spark_session(app_name: str = None) -> SparkSession:
    """Create and configure Spark session with Delta Lake support"""
    config = SparkConfig()
    
    app_name = app_name or config.SPARK_APP_NAME
    
    # Spark configuration
    spark_config = {
        "spark.sql.adaptive.enabled": "true",
        "spark.sql.adaptive.coalescePartitions.enabled": "true",
        "spark.sql.adaptive.coalescePartitions.minPartitionNum": "1",
        "spark.sql.adaptive.coalescePartitions.initialPartitionNum": "10",
        "spark.sql.streaming.metricsEnabled": "true",
        "spark.sql.streaming.ui.enabled": "true",
        "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
        "spark.sql.extensions": "io.delta.sql.DeltaSparkSessionExtension",
        "spark.sql.catalog.spark_catalog": "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        "spark.databricks.delta.retentionDurationCheck.enabled": "false",
        "spark.databricks.delta.merge.repartitionBeforeWrite.enabled": "true",
        "spark.databricks.delta.optimizeWrite.enabled": "true",
        "spark.databricks.delta.autoCompact.enabled": "true",
        
        # Kafka configuration
        "spark.sql.streaming.kafka.useDeprecatedOffsetFetching": "false",
        
        # Checkpoint configuration
        "spark.sql.streaming.checkpointLocation": config.CHECKPOINT_DIR,
        
        # Memory configuration
        "spark.executor.memory": "2g",
        "spark.driver.memory": "1g",
        "spark.executor.memoryFraction": "0.8",
        "spark.executor.cores": "2",
        
        # Network configuration
        "spark.network.timeout": "600s",
        "spark.sql.broadcastTimeout": "600s",
    }
    
    # Create SparkSession builder
    builder = SparkSession.builder \
        .appName(app_name) \
        .master(config.SPARK_MASTER)
    
    # Add configuration
    for key, value in spark_config.items():
        builder = builder.config(key, value)
    
    # Configure Delta Lake
    builder = configure_spark_with_delta_pip(builder, extra_packages=[
        "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0",
        "org.postgresql:postgresql:42.7.1"
    ])
    
    # Create session
    spark = builder.getOrCreate()
    
    # Set log level
    spark.sparkContext.setLogLevel("WARN")
    
    logger.info(f"Spark session created: {app_name}")
    logger.info(f"Spark version: {spark.version}")
    logger.info(f"Delta Lake configured with path: {config.DELTA_LAKE_PATH}")
    
    return spark

def get_kafka_stream_reader(spark: SparkSession, topic: str, starting_offsets: str = "latest"):
    """Create Kafka stream reader"""
    config = SparkConfig()
    
    return spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", config.KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", topic) \
        .option("startingOffsets", starting_offsets) \
        .option("failOnDataLoss", "false") \
        .option("kafka.consumer.timeout.ms", "60000") \
        .option("kafka.request.timeout.ms", "120000") \
        .option("kafka.session.timeout.ms", "60000") \
        .option("maxOffsetsPerTrigger", "1000")

def write_to_delta(df, path: str, mode: str = "append", checkpoint_location: str = None):
    """Write streaming DataFrame to Delta Lake"""
    config = SparkConfig()
    
    full_path = f"{config.DELTA_LAKE_PATH}/{path}"
    checkpoint_path = checkpoint_location or f"{config.CHECKPOINT_DIR}/{path}"
    
    return df.writeStream \
        .format("delta") \
        .outputMode(mode) \
        .option("checkpointLocation", checkpoint_path) \
        .option("path", full_path)

def write_to_postgres(df, table_name: str, mode: str = "append"):
    """Write DataFrame to PostgreSQL"""
    config = SparkConfig()
    
    return df.write \
        .jdbc(
            url=config.postgres_url,
            table=table_name,
            mode=mode,
            properties=config.postgres_properties
        )

def write_stream_to_postgres(df, table_name: str, checkpoint_location: str = None):
    """Write streaming DataFrame to PostgreSQL"""
    config = SparkConfig()
    checkpoint_path = checkpoint_location or f"{config.CHECKPOINT_DIR}/{table_name}"
    
    def write_batch_to_postgres(batch_df, batch_id):
        """Write each micro-batch to PostgreSQL"""
        if batch_df.count() > 0:
            batch_df.write \
                .jdbc(
                    url=config.postgres_url,
                    table=table_name,
                    mode="append",
                    properties=config.postgres_properties
                )
            logger.info(f"Batch {batch_id}: Written {batch_df.count()} records to {table_name}")
    
    return df.writeStream \
        .foreachBatch(write_batch_to_postgres) \
        .option("checkpointLocation", checkpoint_path) \
        .trigger(processingTime='30 seconds')