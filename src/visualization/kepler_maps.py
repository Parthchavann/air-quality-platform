#!/usr/bin/env python3
"""
KeplerGL integration for advanced pollution heatmaps and visualizations
"""

import pandas as pd
import streamlit as st
from keplergl import KeplerGl
import json
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List, Optional
import numpy as np

from database import DatabaseConnection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AirQualityKeplerMaps:
    """Advanced visualizations using KeplerGL for air quality data"""
    
    def __init__(self):
        self.db = DatabaseConnection()
        
        # Default KeplerGL configuration for air quality visualization
        self.kepler_config = {
            "version": "v1",
            "config": {
                "visState": {
                    "filters": [],
                    "layers": [
                        {
                            "id": "air-quality-layer",
                            "type": "heatmap",
                            "config": {
                                "dataId": "air_quality_data",
                                "label": "Air Quality Heatmap",
                                "color": [255, 203, 153],
                                "highlightColor": [252, 242, 26, 255],
                                "columns": {
                                    "lat": "latitude",
                                    "lng": "longitude"
                                },
                                "isVisible": True,
                                "visConfig": {
                                    "opacity": 0.8,
                                    "colorRange": {
                                        "name": "Global Warming",
                                        "type": "sequential",
                                        "category": "Uber",
                                        "colors": [
                                            "#5A1846",
                                            "#900C3F", 
                                            "#C70039",
                                            "#E3611C",
                                            "#F1920E",
                                            "#FFC300"
                                        ]
                                    },
                                    "radius": 20
                                }
                            },
                            "visualChannels": {
                                "weightField": {
                                    "name": "aqi",
                                    "type": "integer"
                                },
                                "weightScale": "linear"
                            }
                        }
                    ],
                    "interactionConfig": {
                        "tooltip": {
                            "fieldsToShow": {
                                "air_quality_data": [
                                    {"name": "city", "format": None},
                                    {"name": "aqi", "format": None},
                                    {"name": "pm25", "format": ".1f"},
                                    {"name": "pm10", "format": ".1f"},
                                    {"name": "timestamp", "format": None}
                                ]
                            }
                        },
                        "brush": {"size": 0.5, "enabled": False},
                        "geocoder": {"enabled": False},
                        "coordinate": {"enabled": False}
                    },
                    "layerBlending": "normal",
                    "splitMaps": [],
                    "animationConfig": {"currentTime": None, "speed": 1}
                },
                "mapState": {
                    "bearing": 0,
                    "dragRotate": False,
                    "latitude": 40.7831,
                    "longitude": -73.9712,
                    "pitch": 0,
                    "zoom": 4,
                    "isSplit": False
                },
                "mapStyle": {
                    "styleType": "dark",
                    "topLayerGroups": {},
                    "visibleLayerGroups": {
                        "label": True,
                        "road": True,
                        "border": False,
                        "building": True,
                        "water": True,
                        "land": True,
                        "3d building": False
                    },
                    "threeDBuildingColor": [9.665468314072013, 17.18305478057247, 31.1442867897876],
                    "mapStyles": {}
                }
            }
        }
    
    def create_pollution_heatmap(self, hours: int = 24) -> KeplerGl:
        """Create interactive pollution heatmap with KeplerGL"""
        
        # Get air quality data
        df = self.db.get_latest_air_quality_data(hours)
        
        if df.empty:
            logger.warning("No data available for heatmap")
            return None
        
        # Prepare data for KeplerGL
        kepler_data = self._prepare_kepler_data(df)
        
        # Create map with data
        map_1 = KeplerGl(height=600, config=self.kepler_config)
        map_1.add_data(data=kepler_data, name='air_quality_data')
        
        return map_1
    
    def create_temporal_heatmap(self, city: str = None, days: int = 7) -> KeplerGl:
        """Create temporal heatmap showing pollution changes over time"""
        
        if city:
            df = self.db.get_city_air_quality_history(city, days)
        else:
            df = self.db.get_latest_air_quality_data(days * 24)
        
        if df.empty:
            logger.warning("No temporal data available")
            return None
        
        # Create temporal configuration
        temporal_config = self._create_temporal_config()
        
        # Prepare data with time component
        kepler_data = self._prepare_temporal_data(df)
        
        # Create temporal map
        map_temporal = KeplerGl(height=600, config=temporal_config)
        map_temporal.add_data(data=kepler_data, name='temporal_air_quality')
        
        return map_temporal
    
    def create_3d_pollution_map(self, hours: int = 24) -> KeplerGl:
        """Create 3D visualization of pollution levels"""
        
        df = self.db.get_latest_air_quality_data(hours)
        
        if df.empty:
            logger.warning("No data available for 3D map")
            return None
        
        # Create 3D configuration
        config_3d = self._create_3d_config()
        
        # Prepare data for 3D visualization
        kepler_data = self._prepare_3d_data(df)
        
        # Create 3D map
        map_3d = KeplerGl(height=700, config=config_3d)
        map_3d.add_data(data=kepler_data, name='pollution_3d')
        
        return map_3d
    
    def create_multi_pollutant_map(self, hours: int = 24) -> KeplerGl:
        """Create map showing multiple pollutants simultaneously"""
        
        df = self.db.get_latest_air_quality_data(hours)
        
        if df.empty:
            logger.warning("No data available for multi-pollutant map")
            return None
        
        # Create multi-layer configuration
        multi_config = self._create_multi_pollutant_config()
        
        # Prepare data for multiple pollutants
        kepler_data = self._prepare_multi_pollutant_data(df)
        
        # Create multi-pollutant map
        map_multi = KeplerGl(height=650, config=multi_config)
        
        # Add separate datasets for each pollutant
        for pollutant in ['pm25', 'pm10', 'no2', 'o3']:
            pollutant_data = kepler_data[kepler_data[f'{pollutant}'].notna()]
            if not pollutant_data.empty:
                map_multi.add_data(data=pollutant_data, name=f'{pollutant}_data')
        
        return map_multi
    
    def create_alert_zones_map(self) -> KeplerGl:
        """Create map showing pollution alert zones"""
        
        # Get alert data
        alerts_df = self.db.get_active_alerts()
        
        if alerts_df.empty:
            st.info("No active alerts to display on map")
            return None
        
        # Get city coordinates for alerts
        city_configs = self.db.get_city_configurations()
        
        # Merge alert data with coordinates
        alert_map_data = alerts_df.merge(
            city_configs[['city', 'latitude', 'longitude']], 
            on='city', 
            how='left'
        )
        
        # Create alerts configuration
        alerts_config = self._create_alerts_config()
        
        # Prepare alert data
        kepler_data = self._prepare_alerts_data(alert_map_data)
        
        # Create alerts map
        map_alerts = KeplerGl(height=600, config=alerts_config)
        map_alerts.add_data(data=kepler_data, name='pollution_alerts')
        
        return map_alerts
    
    def _prepare_kepler_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for basic KeplerGL heatmap"""
        
        # Get latest data point for each city
        latest_data = df.groupby('city').first().reset_index()
        
        # Ensure required columns are present and clean
        kepler_df = latest_data.copy()
        
        # Fill missing values
        numeric_columns = ['pm25', 'pm10', 'co', 'no2', 'o3', 'so2', 'aqi']
        kepler_df[numeric_columns] = kepler_df[numeric_columns].fillna(0)
        
        # Format timestamp
        if 'timestamp' in kepler_df.columns:
            kepler_df['timestamp'] = pd.to_datetime(kepler_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Add pollution level categories
        kepler_df['pollution_level'] = kepler_df['aqi'].apply(self._get_pollution_level)
        
        # Add color coding for visualization
        kepler_df['aqi_color'] = kepler_df['aqi'].apply(self._get_aqi_color_code)
        
        return kepler_df
    
    def _prepare_temporal_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for temporal visualization"""
        
        temporal_df = df.copy()
        
        # Ensure timestamp is datetime
        temporal_df['timestamp'] = pd.to_datetime(temporal_df['timestamp'])
        
        # Add time-based features
        temporal_df['hour'] = temporal_df['timestamp'].dt.hour
        temporal_df['day_of_week'] = temporal_df['timestamp'].dt.day_name()
        temporal_df['unix_timestamp'] = temporal_df['timestamp'].astype('int64') // 10**9
        
        # Fill missing values
        numeric_columns = ['pm25', 'pm10', 'co', 'no2', 'o3', 'so2', 'aqi']
        temporal_df[numeric_columns] = temporal_df[numeric_columns].fillna(0)
        
        return temporal_df
    
    def _prepare_3d_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for 3D visualization"""
        
        data_3d = df.copy()
        
        # Get latest data for each city
        latest_3d = data_3d.groupby('city').first().reset_index()
        
        # Add elevation based on AQI (for 3D effect)
        latest_3d['elevation'] = latest_3d['aqi'] * 10  # Scale for visibility
        
        # Add radius based on PM2.5 levels
        latest_3d['radius'] = np.clip(latest_3d['pm25'] * 100, 100, 1000)
        
        # Fill missing values
        latest_3d = latest_3d.fillna(0)
        
        return latest_3d
    
    def _prepare_multi_pollutant_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for multi-pollutant visualization"""
        
        multi_df = df.copy()
        
        # Get latest data for each city
        latest_multi = multi_df.groupby('city').first().reset_index()
        
        # Normalize pollutant values for better visualization
        pollutants = ['pm25', 'pm10', 'no2', 'o3', 'co', 'so2']
        
        for pollutant in pollutants:
            if pollutant in latest_multi.columns:
                # Create scaled version for visualization
                max_val = latest_multi[pollutant].max()
                if max_val > 0:
                    latest_multi[f'{pollutant}_scaled'] = (latest_multi[pollutant] / max_val) * 100
                else:
                    latest_multi[f'{pollutant}_scaled'] = 0
        
        return latest_multi.fillna(0)
    
    def _prepare_alerts_data(self, alerts_df: pd.DataFrame) -> pd.DataFrame:
        """Prepare alert data for visualization"""
        
        alerts_kepler = alerts_df.copy()
        
        # Add severity numeric values for visualization
        severity_map = {'warning': 1, 'alert': 2, 'critical': 3}
        alerts_kepler['severity_level'] = alerts_kepler['severity'].map(severity_map)
        
        # Add color coding
        color_map = {'warning': '#FFC107', 'alert': '#FF9800', 'critical': '#F44336'}
        alerts_kepler['alert_color'] = alerts_kepler['severity'].map(color_map)
        
        # Format timestamp
        alerts_kepler['timestamp'] = pd.to_datetime(alerts_kepler['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        return alerts_kepler.fillna('')
    
    def _create_temporal_config(self) -> Dict[str, Any]:
        """Create configuration for temporal visualization"""
        
        return {
            "version": "v1",
            "config": {
                "visState": {
                    "filters": [
                        {
                            "dataId": ["temporal_air_quality"],
                            "id": "time_filter",
                            "name": ["unix_timestamp"],
                            "type": "timeRange",
                            "value": [0, 9999999999999],
                            "enlarged": True,
                            "plotType": "histogram",
                            "animationWindow": "free",
                            "yAxis": None
                        }
                    ],
                    "layers": [
                        {
                            "id": "temporal_layer",
                            "type": "point",
                            "config": {
                                "dataId": "temporal_air_quality",
                                "label": "Temporal Air Quality",
                                "columns": {
                                    "lat": "latitude",
                                    "lng": "longitude"
                                },
                                "isVisible": True,
                                "visConfig": {
                                    "radius": 10,
                                    "fixedRadius": False,
                                    "opacity": 0.8,
                                    "outline": False,
                                    "thickness": 2,
                                    "strokeColor": None,
                                    "colorRange": {
                                        "name": "Global Warming",
                                        "type": "sequential",
                                        "category": "Uber",
                                        "colors": ["#5A1846", "#900C3F", "#C70039", "#E3611C", "#F1920E", "#FFC300"]
                                    }
                                }
                            },
                            "visualChannels": {
                                "colorField": {"name": "aqi", "type": "integer"},
                                "colorScale": "quantile",
                                "sizeField": {"name": "pm25", "type": "real"},
                                "sizeScale": "linear"
                            }
                        }
                    ],
                    "animationConfig": {
                        "currentTime": None,
                        "speed": 1
                    }
                }
            }
        }
    
    def _create_3d_config(self) -> Dict[str, Any]:
        """Create configuration for 3D visualization"""
        
        return {
            "version": "v1",
            "config": {
                "visState": {
                    "layers": [
                        {
                            "id": "3d_pollution_layer",
                            "type": "column",
                            "config": {
                                "dataId": "pollution_3d",
                                "label": "3D Pollution Levels",
                                "columns": {
                                    "lat": "latitude",
                                    "lng": "longitude"
                                },
                                "isVisible": True,
                                "visConfig": {
                                    "radius": 1000,
                                    "opacity": 0.8,
                                    "colorRange": {
                                        "name": "Global Warming",
                                        "type": "sequential",
                                        "category": "Uber",
                                        "colors": ["#5A1846", "#900C3F", "#C70039", "#E3611C", "#F1920E", "#FFC300"]
                                    },
                                    "radiusRange": [0, 50],
                                    "elevationScale": 5
                                }
                            },
                            "visualChannels": {
                                "colorField": {"name": "aqi", "type": "integer"},
                                "colorScale": "quantile",
                                "sizeField": {"name": "radius", "type": "real"},
                                "sizeScale": "linear",
                                "heightField": {"name": "elevation", "type": "real"},
                                "heightScale": "linear"
                            }
                        }
                    ]
                },
                "mapState": {
                    "bearing": 0,
                    "dragRotate": True,
                    "latitude": 40.7831,
                    "longitude": -73.9712,
                    "pitch": 50,
                    "zoom": 4
                }
            }
        }
    
    def _create_multi_pollutant_config(self) -> Dict[str, Any]:
        """Create configuration for multi-pollutant visualization"""
        
        return {
            "version": "v1",
            "config": {
                "visState": {
                    "layers": [
                        {
                            "id": "pm25_layer",
                            "type": "point",
                            "config": {
                                "dataId": "pm25_data",
                                "label": "PM2.5",
                                "columns": {"lat": "latitude", "lng": "longitude"},
                                "isVisible": True,
                                "visConfig": {
                                    "radius": 8,
                                    "opacity": 0.7,
                                    "colorRange": {
                                        "name": "ColorBrewer RdYlBu-6",
                                        "type": "diverging",
                                        "colors": ["#d73027", "#fc8d59", "#fee08b", "#e0f3f8", "#91bfdb", "#4575b4"]
                                    }
                                }
                            },
                            "visualChannels": {
                                "colorField": {"name": "pm25", "type": "real"},
                                "colorScale": "quantile"
                            }
                        }
                    ]
                }
            }
        }
    
    def _create_alerts_config(self) -> Dict[str, Any]:
        """Create configuration for alerts visualization"""
        
        return {
            "version": "v1",
            "config": {
                "visState": {
                    "layers": [
                        {
                            "id": "alerts_layer",
                            "type": "icon",
                            "config": {
                                "dataId": "pollution_alerts",
                                "label": "Pollution Alerts",
                                "columns": {"lat": "latitude", "lng": "longitude"},
                                "isVisible": True,
                                "visConfig": {
                                    "radius": 20,
                                    "fixedRadius": False,
                                    "opacity": 0.9,
                                    "colorRange": {
                                        "name": "Custom Alert Colors",
                                        "type": "custom",
                                        "colors": ["#FFC107", "#FF9800", "#F44336"]
                                    }
                                }
                            },
                            "visualChannels": {
                                "colorField": {"name": "severity_level", "type": "integer"},
                                "colorScale": "ordinal",
                                "sizeField": {"name": "value", "type": "real"},
                                "sizeScale": "linear"
                            }
                        }
                    ]
                }
            }
        }
    
    def _get_pollution_level(self, aqi: float) -> str:
        """Get pollution level category"""
        if pd.isna(aqi):
            return "Unknown"
        elif aqi <= 50:
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
    
    def _get_aqi_color_code(self, aqi: float) -> str:
        """Get color code for AQI value"""
        if pd.isna(aqi):
            return "#CCCCCC"
        elif aqi <= 50:
            return "#00E400"  # Good - Green
        elif aqi <= 100:
            return "#FFFF00"  # Moderate - Yellow
        elif aqi <= 150:
            return "#FF7E00"  # Unhealthy for Sensitive Groups - Orange
        elif aqi <= 200:
            return "#FF0000"  # Unhealthy - Red
        elif aqi <= 300:
            return "#8F3F97"  # Very Unhealthy - Purple
        else:
            return "#7E0023"  # Hazardous - Maroon

def create_kepler_dashboard():
    """Create Streamlit interface for KeplerGL visualizations"""
    
    st.header("🗺️ Advanced Air Quality Maps with KeplerGL")
    
    # Initialize KeplerGL maps
    kepler_maps = AirQualityKeplerMaps()
    
    # Map selection
    map_type = st.selectbox(
        "Select Map Type",
        [
            "Pollution Heatmap",
            "Temporal Analysis",
            "3D Pollution Levels", 
            "Multi-Pollutant View",
            "Alert Zones"
        ]
    )
    
    # Time range selector
    col1, col2 = st.columns(2)
    with col1:
        hours = st.slider("Time Range (hours)", 1, 168, 24)
    
    with col2:
        if map_type == "Temporal Analysis":
            days = st.slider("Analysis Period (days)", 1, 30, 7)
        else:
            days = 7
    
    # Generate selected map
    with st.spinner("Generating interactive map..."):
        
        if map_type == "Pollution Heatmap":
            kepler_map = kepler_maps.create_pollution_heatmap(hours)
            st.markdown("### Real-time Pollution Heatmap")
            st.markdown("Interactive heatmap showing current air quality conditions across monitored cities.")
            
        elif map_type == "Temporal Analysis":
            selected_city = st.selectbox(
                "Select City (or leave blank for all cities)",
                ["All Cities"] + list(kepler_maps.db.get_city_configurations()['city'].unique())
            )
            city = None if selected_city == "All Cities" else selected_city
            kepler_map = kepler_maps.create_temporal_heatmap(city, days)
            st.markdown("### Temporal Pollution Analysis")
            st.markdown("Time-based visualization showing how pollution levels change over time.")
            
        elif map_type == "3D Pollution Levels":
            kepler_map = kepler_maps.create_3d_pollution_map(hours)
            st.markdown("### 3D Pollution Visualization")
            st.markdown("Three-dimensional view of pollution levels with height representing pollution intensity.")
            
        elif map_type == "Multi-Pollutant View":
            kepler_map = kepler_maps.create_multi_pollutant_map(hours)
            st.markdown("### Multi-Pollutant Analysis")
            st.markdown("Comparative view of different pollutants across cities.")
            
        elif map_type == "Alert Zones":
            kepler_map = kepler_maps.create_alert_zones_map()
            st.markdown("### Pollution Alert Zones")
            st.markdown("Current active pollution alerts and their locations.")
    
    # Display map
    if kepler_map:
        # Save map as HTML and display
        map_html = kepler_map._repr_html_()
        st.components.v1.html(map_html, height=650)
        
        # Add download option
        if st.button("📥 Download Map Configuration"):
            config_json = json.dumps(kepler_map.config, indent=2)
            st.download_button(
                label="Download JSON Config",
                data=config_json,
                file_name=f"kepler_config_{map_type.lower().replace(' ', '_')}.json",
                mime="application/json"
            )
    else:
        st.warning("No data available for the selected map type and time range.")
    
    # Usage instructions
    with st.expander("📋 Map Usage Instructions"):
        st.markdown("""
        **Interactive Features:**
        - **Pan**: Click and drag to move around the map
        - **Zoom**: Use mouse wheel or zoom controls
        - **Layer Control**: Toggle different layers on/off
        - **Filters**: Use time filters for temporal data
        - **Tooltip**: Hover over points for detailed information
        - **3D Controls**: In 3D mode, use Ctrl+drag to rotate view
        
        **Map Types:**
        - **Heatmap**: Shows pollution density across regions
        - **Temporal**: Time-based analysis with animation controls  
        - **3D**: Three-dimensional pollution towers
        - **Multi-Pollutant**: Compare different pollutants simultaneously
        - **Alerts**: Current active pollution alerts
        """)

if __name__ == "__main__":
    create_kepler_dashboard()