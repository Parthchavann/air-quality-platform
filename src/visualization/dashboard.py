#!/usr/bin/env python3
"""
Streamlit Dashboard for Air Quality Monitoring Platform
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import folium_static, st_folium
from datetime import datetime, timedelta
import logging
import numpy as np
from typing import Dict, List, Any
import altair as alt

from database import DatabaseConnection

# Page configuration
st.set_page_config(
    page_title="Air Quality Monitoring Platform",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #2E86C1;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-critical {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .alert-warning {
        background-color: #fff3e0;
        border-left: 5px solid #ff9800;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .alert-good {
        background-color: #e8f5e8;
        border-left: 5px solid #4caf50;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database connection
@st.cache_resource
def init_database():
    return DatabaseConnection()

def get_aqi_color(aqi_value: float) -> str:
    """Get color based on AQI value"""
    if aqi_value <= 50:
        return '#4CAF50'  # Good - Green
    elif aqi_value <= 100:
        return '#FFEB3B'  # Moderate - Yellow
    elif aqi_value <= 150:
        return '#FF9800'  # Unhealthy for Sensitive Groups - Orange
    elif aqi_value <= 200:
        return '#F44336'  # Unhealthy - Red
    elif aqi_value <= 300:
        return '#9C27B0'  # Very Unhealthy - Purple
    else:
        return '#8B0000'  # Hazardous - Maroon

def get_aqi_category(aqi_value: float) -> str:
    """Get AQI category description"""
    if aqi_value <= 50:
        return 'Good'
    elif aqi_value <= 100:
        return 'Moderate'
    elif aqi_value <= 150:
        return 'Unhealthy for Sensitive Groups'
    elif aqi_value <= 200:
        return 'Unhealthy'
    elif aqi_value <= 300:
        return 'Very Unhealthy'
    else:
        return 'Hazardous'

def create_pollution_map(df: pd.DataFrame) -> folium.Map:
    """Create interactive pollution map"""
    if df.empty:
        # Default map centered on US
        return folium.Map(location=[39.8283, -98.5795], zoom_start=4)
    
    # Get the center point
    center_lat = df['latitude'].mean()
    center_lon = df['longitude'].mean()
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=4)
    
    # Add markers for each city
    for _, row in df.iterrows():
        if pd.notna(row['latitude']) and pd.notna(row['longitude']) and pd.notna(row['aqi']):
            aqi = row['aqi']
            color = get_aqi_color(aqi)
            category = get_aqi_category(aqi)
            
            # Create popup content
            popup_content = f"""
            <b>{row['city']}, {row['country']}</b><br>
            AQI: {aqi} ({category})<br>
            PM2.5: {row['pm25']:.1f} µg/m³<br>
            PM10: {row['pm10']:.1f} µg/m³<br>
            Last Updated: {row['timestamp'].strftime('%Y-%m-%d %H:%M')}
            """
            
            # Add circle marker
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=max(8, min(20, aqi / 10)),  # Size based on AQI
                popup=popup_content,
                color='black',
                fillColor=color,
                fillOpacity=0.7,
                weight=2
            ).add_to(m)
    
    # Add legend
    legend_html = """
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: 120px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <p><b>Air Quality Index</b></p>
    <p><i class="fa fa-circle" style="color:#4CAF50"></i> Good (0-50)</p>
    <p><i class="fa fa-circle" style="color:#FFEB3B"></i> Moderate (51-100)</p>
    <p><i class="fa fa-circle" style="color:#FF9800"></i> Unhealthy for Sensitive (101-150)</p>
    <p><i class="fa fa-circle" style="color:#F44336"></i> Unhealthy (151-200)</p>
    <p><i class="fa fa-circle" style="color:#9C27B0"></i> Very Unhealthy (201-300)</p>
    <p><i class="fa fa-circle" style="color:#8B0000"></i> Hazardous (300+)</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def create_time_series_chart(df: pd.DataFrame, pollutant: str, cities: List[str]) -> go.Figure:
    """Create time series chart for pollutant levels"""
    if df.empty:
        return go.Figure()
    
    fig = go.Figure()
    
    # Filter for selected cities
    if cities:
        df = df[df['city'].isin(cities)]
    
    # Add line for each city
    for city in df['city'].unique():
        city_data = df[df['city'] == city].sort_values('timestamp')
        
        fig.add_trace(go.Scatter(
            x=city_data['timestamp'],
            y=city_data[pollutant],
            mode='lines+markers',
            name=city,
            line=dict(width=2),
            hovertemplate=f'<b>{city}</b><br>Time: %{{x}}<br>{pollutant.upper()}: %{{y}}<extra></extra>'
        ))
    
    # Update layout
    fig.update_layout(
        title=f'{pollutant.upper()} Levels Over Time',
        xaxis_title='Time',
        yaxis_title=f'{pollutant.upper()} Concentration',
        hovermode='x unified',
        height=400,
        showlegend=True
    )
    
    return fig

def create_correlation_heatmap(df: pd.DataFrame) -> go.Figure:
    """Create correlation heatmap between pollutants and weather"""
    if df.empty:
        return go.Figure()
    
    # Select numeric columns for correlation
    numeric_cols = ['pm25', 'pm10', 'co', 'no2', 'o3', 'so2', 'aqi']
    
    # Calculate correlation matrix
    corr_matrix = df[numeric_cols].corr()
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='RdBu',
        zmid=0,
        text=np.round(corr_matrix.values, 2),
        texttemplate="%{text}",
        textfont={"size": 10},
        hoverongaps=False
    ))
    
    fig.update_layout(
        title='Pollutant Correlation Matrix',
        height=400
    )
    
    return fig

def display_alerts(alerts_df: pd.DataFrame):
    """Display active pollution alerts"""
    if alerts_df.empty:
        st.success("🟢 No active pollution alerts")
        return
    
    st.subheader("🚨 Active Pollution Alerts")
    
    for _, alert in alerts_df.iterrows():
        severity = alert['severity']
        
        if severity == 'critical':
            css_class = 'alert-critical'
            icon = '🔴'
        elif severity == 'alert':
            css_class = 'alert-warning'
            icon = '🟡'
        else:
            css_class = 'alert-warning'
            icon = '🟠'
        
        st.markdown(f"""
        <div class="{css_class}">
            <h4>{icon} {alert['city']} - {alert['pollutant'].upper()} Alert</h4>
            <p><strong>Severity:</strong> {severity.upper()}</p>
            <p><strong>Value:</strong> {alert['value']:.1f} (Threshold: {alert['threshold']:.1f})</p>
            <p><strong>Message:</strong> {alert['message']}</p>
            <p><strong>Time:</strong> {alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """, unsafe_allow_html=True)

def display_city_metrics(df: pd.DataFrame, city: str):
    """Display key metrics for a selected city"""
    city_data = df[df['city'] == city]
    
    if city_data.empty:
        st.warning(f"No data available for {city}")
        return
    
    # Get latest data
    latest = city_data.sort_values('timestamp').iloc[-1]
    
    # Create columns for metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        aqi_color = get_aqi_color(latest['aqi']) if pd.notna(latest['aqi']) else '#CCCCCC'
        st.markdown(f"""
        <div class="metric-container" style="border-left: 5px solid {aqi_color};">
            <h3>Air Quality Index</h3>
            <h2>{latest['aqi']:.0f}</h2>
            <p>{get_aqi_category(latest['aqi'])}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        pm25_val = latest['pm25'] if pd.notna(latest['pm25']) else 0
        st.markdown(f"""
        <div class="metric-container">
            <h3>PM2.5</h3>
            <h2>{pm25_val:.1f}</h2>
            <p>µg/m³</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        pm10_val = latest['pm10'] if pd.notna(latest['pm10']) else 0
        st.markdown(f"""
        <div class="metric-container">
            <h3>PM10</h3>
            <h2>{pm10_val:.1f}</h2>
            <p>µg/m³</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        no2_val = latest['no2'] if pd.notna(latest['no2']) else 0
        st.markdown(f"""
        <div class="metric-container">
            <h3>NO₂</h3>
            <h2>{no2_val:.1f}</h2>
            <p>µg/m³</p>
        </div>
        """, unsafe_allow_html=True)

def main():
    """Main dashboard application"""
    
    # Header
    st.markdown('<h1 class="main-header">🌍 Air Quality Monitoring Platform</h1>', unsafe_allow_html=True)
    
    # Initialize database
    db = init_database()
    
    # Sidebar
    st.sidebar.header("Dashboard Controls")
    
    # Time range selector
    time_range = st.sidebar.selectbox(
        "Select Time Range",
        ["Last 6 hours", "Last 12 hours", "Last 24 hours", "Last 3 days", "Last 7 days"]
    )
    
    # Map time range to hours
    time_mapping = {
        "Last 6 hours": 6,
        "Last 12 hours": 12,
        "Last 24 hours": 24,
        "Last 3 days": 72,
        "Last 7 days": 168
    }
    hours = time_mapping[time_range]
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Load data
    with st.spinner("Loading air quality data..."):
        air_quality_df = db.get_latest_air_quality_data(hours)
        weather_df = db.get_weather_data(hours)
        alerts_df = db.get_active_alerts()
        stats = db.get_data_quality_stats()
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🌍 Overview", "📊 Analytics", "🗺️ Map View", "🚨 Alerts", "📈 Data Quality", "🔬 Advanced Maps"])
    
    with tab1:
        st.header("Real-Time Air Quality Overview")
        
        # Display alerts
        display_alerts(alerts_df)
        
        # Key statistics
        if not air_quality_df.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_aqi = air_quality_df['aqi'].mean()
                st.metric("Average AQI", f"{avg_aqi:.1f}", delta=None)
            
            with col2:
                cities_count = air_quality_df['city'].nunique()
                st.metric("Cities Monitored", cities_count)
            
            with col3:
                latest_update = air_quality_df['timestamp'].max()
                time_diff = datetime.now() - latest_update.tz_localize(None) if latest_update.tz else datetime.now() - latest_update
                st.metric("Last Update", f"{int(time_diff.total_seconds() / 60)} min ago")
            
            with col4:
                critical_alerts = len(alerts_df[alerts_df['severity'] == 'critical'])
                st.metric("Critical Alerts", critical_alerts)
        
        # City selector
        if not air_quality_df.empty:
            st.subheader("City Details")
            selected_city = st.selectbox(
                "Select a city to view details:",
                air_quality_df['city'].unique()
            )
            
            if selected_city:
                display_city_metrics(air_quality_df, selected_city)
                
                # Show recent trends
                city_history = db.get_city_air_quality_history(selected_city, days=1)
                if not city_history.empty:
                    st.subheader(f"Recent Trends - {selected_city}")
                    
                    # Create multi-pollutant chart
                    fig = make_subplots(
                        rows=2, cols=2,
                        subplot_titles=('PM2.5', 'PM10', 'NO₂', 'AQI'),
                        specs=[[{"secondary_y": False}, {"secondary_y": False}],
                               [{"secondary_y": False}, {"secondary_y": False}]]
                    )
                    
                    fig.add_trace(
                        go.Scatter(x=city_history['timestamp'], y=city_history['pm25'], name='PM2.5'),
                        row=1, col=1
                    )
                    fig.add_trace(
                        go.Scatter(x=city_history['timestamp'], y=city_history['pm10'], name='PM10'),
                        row=1, col=2
                    )
                    fig.add_trace(
                        go.Scatter(x=city_history['timestamp'], y=city_history['no2'], name='NO₂'),
                        row=2, col=1
                    )
                    fig.add_trace(
                        go.Scatter(x=city_history['timestamp'], y=city_history['aqi'], name='AQI'),
                        row=2, col=2
                    )
                    
                    fig.update_layout(height=500, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("Air Quality Analytics")
        
        if not air_quality_df.empty:
            # City comparison
            st.subheader("City Comparison")
            
            # Multi-select for cities
            selected_cities = st.multiselect(
                "Select cities to compare:",
                air_quality_df['city'].unique(),
                default=air_quality_df['city'].unique()[:4]  # Default to first 4 cities
            )
            
            if selected_cities:
                # Pollutant selector
                pollutant = st.selectbox(
                    "Select pollutant:",
                    ['pm25', 'pm10', 'co', 'no2', 'o3', 'so2', 'aqi']
                )
                
                # Time series chart
                time_series_fig = create_time_series_chart(air_quality_df, pollutant, selected_cities)
                st.plotly_chart(time_series_fig, use_container_width=True)
                
                # Box plot for distribution
                filtered_df = air_quality_df[air_quality_df['city'].isin(selected_cities)]
                box_fig = px.box(
                    filtered_df, 
                    x='city', 
                    y=pollutant,
                    title=f'{pollutant.upper()} Distribution by City',
                    color='city'
                )
                st.plotly_chart(box_fig, use_container_width=True)
            
            # Correlation analysis
            st.subheader("Pollutant Correlations")
            corr_fig = create_correlation_heatmap(air_quality_df)
            st.plotly_chart(corr_fig, use_container_width=True)
    
    with tab3:
        st.header("Global Air Quality Map")
        
        if not air_quality_df.empty:
            # Get latest data for each city
            latest_data = air_quality_df.groupby('city').first().reset_index()
            
            # Create and display map
            pollution_map = create_pollution_map(latest_data)
            folium_static(pollution_map)
            
            # Summary table
            st.subheader("Current Conditions Summary")
            summary_df = latest_data[['city', 'country', 'aqi', 'pm25', 'pm10', 'timestamp']].copy()
            summary_df['aqi_category'] = summary_df['aqi'].apply(get_aqi_category)
            summary_df = summary_df.sort_values('aqi', ascending=False)
            
            st.dataframe(
                summary_df,
                use_container_width=True,
                column_config={
                    "aqi": st.column_config.NumberColumn(
                        "AQI",
                        format="%.0f",
                    ),
                    "pm25": st.column_config.NumberColumn(
                        "PM2.5 (µg/m³)",
                        format="%.1f",
                    ),
                    "pm10": st.column_config.NumberColumn(
                        "PM10 (µg/m³)",
                        format="%.1f",
                    ),
                }
            )
    
    with tab4:
        st.header("Pollution Alerts & Notifications")
        
        # Display all alerts (not just active ones)
        all_alerts = db.get_active_alerts()  # This can be modified to get all recent alerts
        
        if not all_alerts.empty:
            # Alert summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                critical_count = len(all_alerts[all_alerts['severity'] == 'critical'])
                st.metric("Critical Alerts", critical_count)
            
            with col2:
                alert_count = len(all_alerts[all_alerts['severity'] == 'alert'])
                st.metric("High Alerts", alert_count)
            
            with col3:
                warning_count = len(all_alerts[all_alerts['severity'] == 'warning'])
                st.metric("Warnings", warning_count)
            
            # Alert timeline
            st.subheader("Alert Timeline")
            
            # Create timeline chart
            if not all_alerts.empty:
                timeline_fig = px.scatter(
                    all_alerts,
                    x='timestamp',
                    y='city',
                    color='severity',
                    size='value',
                    hover_data=['pollutant', 'value', 'threshold', 'message'],
                    title='Pollution Alerts Timeline',
                    color_discrete_map={
                        'critical': '#F44336',
                        'alert': '#FF9800',
                        'warning': '#FFC107'
                    }
                )
                st.plotly_chart(timeline_fig, use_container_width=True)
            
            # Detailed alerts
            display_alerts(all_alerts)
        else:
            st.success("🎉 No pollution alerts in the selected time range!")
    
    with tab5:
        st.header("Data Quality & System Status")
        
        if stats:
            # System statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("Air Quality Data")
                aq_stats = stats.get('air_quality', {})
                st.metric("Total Measurements (24h)", aq_stats.get('total_measurements', 0))
                st.metric("Cities Reporting", aq_stats.get('cities_count', 0))
                if aq_stats.get('latest_measurement'):
                    st.write(f"Latest: {aq_stats['latest_measurement']}")
            
            with col2:
                st.subheader("Weather Data")
                weather_stats = stats.get('weather', {})
                st.metric("Weather Measurements (24h)", weather_stats.get('total_measurements', 0))
                if weather_stats.get('latest_measurement'):
                    st.write(f"Latest: {weather_stats['latest_measurement']}")
            
            with col3:
                st.subheader("Alert System")
                alert_stats = stats.get('alerts', {})
                st.metric("Total Alerts (24h)", alert_stats.get('total_alerts', 0))
                st.metric("Active Alerts", alert_stats.get('active_alerts', 0))
        
        # Data freshness indicator
        st.subheader("Data Freshness")
        if not air_quality_df.empty:
            latest_timestamp = air_quality_df['timestamp'].max()
            current_time = datetime.now()
            
            if latest_timestamp.tz:
                time_diff = current_time - latest_timestamp.tz_localize(None)
            else:
                time_diff = current_time - latest_timestamp
            
            minutes_ago = int(time_diff.total_seconds() / 60)
            
            if minutes_ago < 10:
                st.success(f"✅ Data is fresh (last update: {minutes_ago} minutes ago)")
            elif minutes_ago < 30:
                st.warning(f"⚠️ Data is moderately fresh (last update: {minutes_ago} minutes ago)")
            else:
                st.error(f"❌ Data is stale (last update: {minutes_ago} minutes ago)")
        
        # Data coverage by city
        if not air_quality_df.empty:
            st.subheader("Data Coverage by City")
            coverage_data = air_quality_df.groupby('city').agg({
                'timestamp': 'count',
                'pm25': lambda x: x.notna().sum(),
                'pm10': lambda x: x.notna().sum(),
                'aqi': lambda x: x.notna().sum()
            }).reset_index()
            
            coverage_data.columns = ['City', 'Total Records', 'PM2.5 Coverage', 'PM10 Coverage', 'AQI Coverage']
            st.dataframe(coverage_data, use_container_width=True)
    
    with tab6:
        st.header("Advanced Interactive Maps")
        
        # Import KeplerGL integration
        try:
            from kepler_maps import create_kepler_dashboard
            create_kepler_dashboard()
        except ImportError as e:
            st.error(f"KeplerGL maps not available: {e}")
            st.info("Install keplergl to enable advanced mapping features")
        except Exception as e:
            st.error(f"Error loading advanced maps: {e}")
            st.info("Check that all services are running and data is available")

if __name__ == "__main__":
    main()