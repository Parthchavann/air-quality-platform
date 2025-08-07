#!/usr/bin/env python3
"""
Data Quality validation using Great Expectations
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
import great_expectations as gx
from great_expectations.core.batch import RuntimeBatchRequest
from great_expectations.checkpoint import SimpleCheckpoint
from great_expectations.data_context import DataContext
from great_expectations.data_context.types.base import DataContextConfig, DatasourceConfig
import psycopg2
from sqlalchemy import create_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AirQualityDataValidator:
    """Data quality validator for air quality data using Great Expectations"""
    
    def __init__(self):
        self.postgres_url = self._get_postgres_url()
        self.engine = create_engine(self.postgres_url)
        self.context = self._init_data_context()
        
        # Create expectation suites
        self._create_expectation_suites()
    
    def _get_postgres_url(self) -> str:
        """Get PostgreSQL connection URL"""
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = os.getenv('POSTGRES_PORT', '5432')
        database = os.getenv('POSTGRES_DB', 'airquality')
        username = os.getenv('POSTGRES_USER', 'airquality_user')
        password = os.getenv('POSTGRES_PASSWORD', 'secure_password')
        
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    def _init_data_context(self) -> DataContext:
        """Initialize Great Expectations data context"""
        
        # Configure datasource
        datasource_config = {
            "name": "air_quality_postgres",
            "class_name": "Datasource",
            "module_name": "great_expectations.datasource",
            "execution_engine": {
                "module_name": "great_expectations.execution_engine",
                "class_name": "SqlAlchemyExecutionEngine",
                "connection_string": self.postgres_url,
            },
            "data_connectors": {
                "default_runtime_data_connector": {
                    "class_name": "RuntimeDataConnector",
                    "module_name": "great_expectations.datasource.data_connector",
                    "batch_identifiers": ["default_identifier_name"],
                },
                "default_inferred_data_connector": {
                    "class_name": "InferredAssetSqlDataConnector",
                    "module_name": "great_expectations.datasource.data_connector",
                    "include_schema_name": True,
                },
            },
        }
        
        # Create data context config
        data_context_config = DataContextConfig(
            datasources={
                "air_quality_postgres": DatasourceConfig(**datasource_config)
            },
            store_backend_defaults={
                "expectations_store": {
                    "class_name": "ExpectationsStore",
                    "store_backend": {
                        "class_name": "TupleFilesystemStoreBackend",
                        "base_directory": "/tmp/great_expectations/expectations/",
                    },
                },
                "validations_store": {
                    "class_name": "ValidationsStore",
                    "store_backend": {
                        "class_name": "TupleFilesystemStoreBackend",
                        "base_directory": "/tmp/great_expectations/validations/",
                    },
                },
                "evaluation_parameter_store": {
                    "class_name": "EvaluationParameterStore"
                },
            },
        )
        
        # Create context
        context = gx.get_context(project_config=data_context_config)
        
        # Add datasource to context
        context.add_datasource(**datasource_config)
        
        return context
    
    def _create_expectation_suites(self):
        """Create expectation suites for data validation"""
        
        # Air quality measurements expectations
        self._create_air_quality_suite()
        
        # Weather data expectations
        self._create_weather_suite()
        
        # Alert data expectations
        self._create_alerts_suite()
    
    def _create_air_quality_suite(self):
        """Create expectation suite for air quality measurements"""
        
        suite_name = "air_quality_measurements_suite"
        
        try:
            # Create or get existing suite
            suite = self.context.create_expectation_suite(
                expectation_suite_name=suite_name,
                overwrite_existing=True
            )
            
            # Basic structure expectations
            suite.add_expectation({
                "expectation_type": "expect_table_columns_to_match_ordered_list",
                "kwargs": {
                    "column_list": [
                        "id", "city", "country", "latitude", "longitude", 
                        "timestamp", "pm25", "pm10", "co", "no2", "o3", 
                        "so2", "aqi", "aqi_category", "source", "created_at"
                    ]
                }
            })
            
            # City should not be null
            suite.add_expectation({
                "expectation_type": "expect_column_values_to_not_be_null",
                "kwargs": {"column": "city"}
            })
            
            # Timestamp should not be null
            suite.add_expectation({
                "expectation_type": "expect_column_values_to_not_be_null",
                "kwargs": {"column": "timestamp"}
            })
            
            # PM2.5 should be between 0 and 500
            suite.add_expectation({
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": "pm25",
                    "min_value": 0,
                    "max_value": 500,
                    "mostly": 0.95  # Allow 5% outliers
                }
            })
            
            # PM10 should be between 0 and 600
            suite.add_expectation({
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": "pm10",
                    "min_value": 0,
                    "max_value": 600,
                    "mostly": 0.95
                }
            })
            
            # AQI should be between 0 and 500
            suite.add_expectation({
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": "aqi",
                    "min_value": 0,
                    "max_value": 500,
                    "mostly": 0.95
                }
            })
            
            # CO should be positive
            suite.add_expectation({
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": "co",
                    "min_value": 0,
                    "max_value": 50,
                    "mostly": 0.95
                }
            })
            
            # Latitude should be between -90 and 90
            suite.add_expectation({
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": "latitude",
                    "min_value": -90,
                    "max_value": 90
                }
            })
            
            # Longitude should be between -180 and 180
            suite.add_expectation({
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": "longitude",
                    "min_value": -180,
                    "max_value": 180
                }
            })
            
            # AQI category should be in valid set
            suite.add_expectation({
                "expectation_type": "expect_column_values_to_be_in_set",
                "kwargs": {
                    "column": "aqi_category",
                    "value_set": [
                        "Good", "Moderate", "Unhealthy for Sensitive Groups",
                        "Unhealthy", "Very Unhealthy", "Hazardous"
                    ],
                    "mostly": 0.9
                }
            })
            
            # Source should be in valid set
            suite.add_expectation({
                "expectation_type": "expect_column_values_to_be_in_set",
                "kwargs": {
                    "column": "source",
                    "value_set": ["openaq", "iqair", "simulated", "openweathermap"],
                    "mostly": 0.95
                }
            })
            
            # Save suite
            self.context.save_expectation_suite(suite)
            logger.info("Air quality expectation suite created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create air quality expectation suite: {e}")
    
    def _create_weather_suite(self):
        """Create expectation suite for weather data"""
        
        suite_name = "weather_data_suite"
        
        try:
            suite = self.context.create_expectation_suite(
                expectation_suite_name=suite_name,
                overwrite_existing=True
            )
            
            # City should not be null
            suite.add_expectation({
                "expectation_type": "expect_column_values_to_not_be_null",
                "kwargs": {"column": "city"}
            })
            
            # Temperature should be reasonable (-50 to 60 Celsius)
            suite.add_expectation({
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": "temperature",
                    "min_value": -50,
                    "max_value": 60,
                    "mostly": 0.95
                }
            })
            
            # Humidity should be between 0 and 100
            suite.add_expectation({
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": "humidity",
                    "min_value": 0,
                    "max_value": 100,
                    "mostly": 0.95
                }
            })
            
            # Pressure should be reasonable (900 to 1100 hPa)
            suite.add_expectation({
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": "pressure",
                    "min_value": 900,
                    "max_value": 1100,
                    "mostly": 0.95
                }
            })
            
            # Wind speed should be positive and reasonable (0 to 100 m/s)
            suite.add_expectation({
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": "wind_speed",
                    "min_value": 0,
                    "max_value": 100,
                    "mostly": 0.95
                }
            })
            
            self.context.save_expectation_suite(suite)
            logger.info("Weather expectation suite created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create weather expectation suite: {e}")
    
    def _create_alerts_suite(self):
        """Create expectation suite for alerts data"""
        
        suite_name = "pollution_alerts_suite"
        
        try:
            suite = self.context.create_expectation_suite(
                expectation_suite_name=suite_name,
                overwrite_existing=True
            )
            
            # City should not be null
            suite.add_expectation({
                "expectation_type": "expect_column_values_to_not_be_null",
                "kwargs": {"column": "city"}
            })
            
            # Severity should be in valid set
            suite.add_expectation({
                "expectation_type": "expect_column_values_to_be_in_set",
                "kwargs": {
                    "column": "severity",
                    "value_set": ["warning", "alert", "critical"]
                }
            })
            
            # Value should be positive
            suite.add_expectation({
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": "value",
                    "min_value": 0,
                    "max_value": 1000,
                    "mostly": 0.95
                }
            })
            
            # Threshold should be positive
            suite.add_expectation({
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": "threshold",
                    "min_value": 0,
                    "max_value": 1000,
                    "mostly": 0.95
                }
            })
            
            self.context.save_expectation_suite(suite)
            logger.info("Alerts expectation suite created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create alerts expectation suite: {e}")
    
    def validate_air_quality_data(self, hours_back: int = 1) -> Dict[str, Any]:
        """Validate recent air quality data"""
        
        # Create batch request for recent data
        batch_request = RuntimeBatchRequest(
            datasource_name="air_quality_postgres",
            data_connector_name="default_runtime_data_connector",
            data_asset_name="air_quality_recent",
            runtime_parameters={
                "query": f"""
                SELECT * FROM air_quality_measurements 
                WHERE timestamp >= NOW() - INTERVAL '{hours_back} hours'
                """
            },
            batch_identifiers={"default_identifier_name": "air_quality_validation"}
        )
        
        # Create checkpoint
        checkpoint_config = {
            "name": "air_quality_checkpoint",
            "config_version": 1.0,
            "template_name": None,
            "module_name": "great_expectations.checkpoint",
            "class_name": "SimpleCheckpoint",
            "run_name_template": "%Y%m%d-%H%M%S-air-quality-validation",
            "expectation_suite_name": "air_quality_measurements_suite",
            "batch_request": batch_request,
            "action_list": [
                {
                    "name": "store_validation_result",
                    "action": {"class_name": "StoreValidationResultAction"},
                },
            ],
        }
        
        # Run validation
        try:
            checkpoint = SimpleCheckpoint(
                f"air_quality_checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                self.context,
                **checkpoint_config
            )
            
            result = checkpoint.run()
            
            validation_result = {
                "success": result.success,
                "statistics": result.run_results,
                "timestamp": datetime.now(),
                "data_asset": "air_quality_measurements",
                "records_validated": self._get_record_count(hours_back, "air_quality_measurements")
            }
            
            logger.info(f"Air quality validation completed: Success={result.success}")
            return validation_result
            
        except Exception as e:
            logger.error(f"Air quality validation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(),
                "data_asset": "air_quality_measurements"
            }
    
    def validate_weather_data(self, hours_back: int = 1) -> Dict[str, Any]:
        """Validate recent weather data"""
        
        batch_request = RuntimeBatchRequest(
            datasource_name="air_quality_postgres",
            data_connector_name="default_runtime_data_connector",
            data_asset_name="weather_recent",
            runtime_parameters={
                "query": f"""
                SELECT * FROM weather_data 
                WHERE timestamp >= NOW() - INTERVAL '{hours_back} hours'
                """
            },
            batch_identifiers={"default_identifier_name": "weather_validation"}
        )
        
        checkpoint_config = {
            "name": "weather_checkpoint",
            "config_version": 1.0,
            "template_name": None,
            "module_name": "great_expectations.checkpoint",
            "class_name": "SimpleCheckpoint",
            "run_name_template": "%Y%m%d-%H%M%S-weather-validation",
            "expectation_suite_name": "weather_data_suite",
            "batch_request": batch_request,
            "action_list": [
                {
                    "name": "store_validation_result",
                    "action": {"class_name": "StoreValidationResultAction"},
                },
            ],
        }
        
        try:
            checkpoint = SimpleCheckpoint(
                f"weather_checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                self.context,
                **checkpoint_config
            )
            
            result = checkpoint.run()
            
            validation_result = {
                "success": result.success,
                "statistics": result.run_results,
                "timestamp": datetime.now(),
                "data_asset": "weather_data",
                "records_validated": self._get_record_count(hours_back, "weather_data")
            }
            
            logger.info(f"Weather validation completed: Success={result.success}")
            return validation_result
            
        except Exception as e:
            logger.error(f"Weather validation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(),
                "data_asset": "weather_data"
            }
    
    def _get_record_count(self, hours_back: int, table_name: str) -> int:
        """Get count of records for validation"""
        try:
            query = f"""
            SELECT COUNT(*) FROM {table_name} 
            WHERE timestamp >= NOW() - INTERVAL '{hours_back} hours'
            """
            
            with self.engine.connect() as conn:
                result = conn.execute(query)
                count = result.scalar()
                return count or 0
                
        except Exception as e:
            logger.error(f"Failed to get record count: {e}")
            return 0
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        
        logger.info("Starting full data validation suite")
        
        validation_results = {
            "timestamp": datetime.now(),
            "overall_success": True,
            "validations": {}
        }
        
        # Validate air quality data
        aq_result = self.validate_air_quality_data()
        validation_results["validations"]["air_quality"] = aq_result
        if not aq_result["success"]:
            validation_results["overall_success"] = False
        
        # Validate weather data
        weather_result = self.validate_weather_data()
        validation_results["validations"]["weather"] = weather_result
        if not weather_result["success"]:
            validation_results["overall_success"] = False
        
        logger.info(f"Full validation completed: Overall Success={validation_results['overall_success']}")
        
        return validation_results
    
    def generate_data_quality_report(self) -> Dict[str, Any]:
        """Generate comprehensive data quality report"""
        
        report = {
            "timestamp": datetime.now(),
            "validation_results": self.run_full_validation(),
            "data_freshness": self._check_data_freshness(),
            "completeness_stats": self._get_completeness_stats(),
            "anomaly_detection": self._detect_anomalies()
        }
        
        return report
    
    def _check_data_freshness(self) -> Dict[str, Any]:
        """Check data freshness"""
        freshness = {}
        
        tables = ["air_quality_measurements", "weather_data", "pollution_alerts"]
        
        for table in tables:
            try:
                query = f"SELECT MAX(timestamp) as latest FROM {table}"
                with self.engine.connect() as conn:
                    result = conn.execute(query)
                    latest = result.scalar()
                    
                    if latest:
                        time_diff = datetime.now() - latest.replace(tzinfo=None)
                        freshness[table] = {
                            "latest_timestamp": latest,
                            "minutes_ago": int(time_diff.total_seconds() / 60),
                            "is_fresh": time_diff.total_seconds() < 1800  # 30 minutes
                        }
                    else:
                        freshness[table] = {
                            "latest_timestamp": None,
                            "minutes_ago": None,
                            "is_fresh": False
                        }
                        
            except Exception as e:
                freshness[table] = {"error": str(e)}
        
        return freshness
    
    def _get_completeness_stats(self) -> Dict[str, Any]:
        """Get data completeness statistics"""
        try:
            query = """
            SELECT 
                city,
                COUNT(*) as total_records,
                COUNT(pm25) as pm25_count,
                COUNT(pm10) as pm10_count,
                COUNT(aqi) as aqi_count,
                COUNT(timestamp) as timestamp_count
            FROM air_quality_measurements 
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
            GROUP BY city
            """
            
            df = pd.read_sql(query, self.engine)
            
            completeness = {}
            for _, row in df.iterrows():
                city = row['city']
                total = row['total_records']
                
                completeness[city] = {
                    "total_records": int(total),
                    "pm25_completeness": (row['pm25_count'] / total * 100) if total > 0 else 0,
                    "pm10_completeness": (row['pm10_count'] / total * 100) if total > 0 else 0,
                    "aqi_completeness": (row['aqi_count'] / total * 100) if total > 0 else 0
                }
            
            return completeness
            
        except Exception as e:
            logger.error(f"Failed to get completeness stats: {e}")
            return {}
    
    def _detect_anomalies(self) -> Dict[str, Any]:
        """Detect data anomalies"""
        try:
            # Get recent data for anomaly detection
            query = """
            SELECT city, pm25, pm10, aqi, timestamp
            FROM air_quality_measurements 
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
            AND pm25 IS NOT NULL AND aqi IS NOT NULL
            """
            
            df = pd.read_sql(query, self.engine)
            
            anomalies = {}
            
            for city in df['city'].unique():
                city_data = df[df['city'] == city]
                
                city_anomalies = []
                
                # Check for extreme values
                if city_data['pm25'].max() > 200:
                    city_anomalies.append(f"Extreme PM2.5 value: {city_data['pm25'].max()}")
                
                if city_data['aqi'].max() > 300:
                    city_anomalies.append(f"Extreme AQI value: {city_data['aqi'].max()}")
                
                # Check for sudden spikes (more than 3 standard deviations)
                if len(city_data) > 5:
                    pm25_mean = city_data['pm25'].mean()
                    pm25_std = city_data['pm25'].std()
                    
                    if pm25_std > 0:
                        outliers = city_data[abs(city_data['pm25'] - pm25_mean) > 3 * pm25_std]
                        if not outliers.empty:
                            city_anomalies.append(f"PM2.5 statistical outliers detected: {len(outliers)} records")
                
                anomalies[city] = city_anomalies
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Failed to detect anomalies: {e}")
            return {}

def main():
    """Main function for standalone execution"""
    validator = AirQualityDataValidator()
    
    # Run full validation
    results = validator.run_full_validation()
    
    print("Data Quality Validation Results:")
    print(f"Overall Success: {results['overall_success']}")
    
    for validation_name, result in results['validations'].items():
        print(f"\n{validation_name.title()} Validation:")
        print(f"  Success: {result['success']}")
        print(f"  Records Validated: {result.get('records_validated', 'N/A')}")
        if not result['success'] and 'error' in result:
            print(f"  Error: {result['error']}")

if __name__ == "__main__":
    main()