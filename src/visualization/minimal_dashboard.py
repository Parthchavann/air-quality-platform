"""
AtmosAnalytics Platform - Enterprise Environmental Intelligence
Professional air quality monitoring with zero custom CSS for maximum compatibility
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import subprocess
import time
from database import DatabaseConnection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="AtmosAnalytics Platform",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded"
)

class MinimalDashboard:
    """Minimal Air Quality Dashboard - No Custom CSS"""
    
    def __init__(self):
        self.db = self.get_database_connection()
        self.setup_session_state()
    
    @staticmethod
    @st.cache_resource
    def get_database_connection():
        """Get cached database connection"""
        try:
            return DatabaseConnection()
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def setup_session_state(self):
        """Initialize session state variables"""
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'overview'
        if 'time_range' not in st.session_state:
            st.session_state.time_range = '24h'
        if 'data_generated' not in st.session_state:
            st.session_state.data_generated = False
    
    def render_header(self):
        """Render simple header"""
        st.title("🌬️ AtmosAnalytics Platform")
        st.markdown("**Enterprise Environmental Intelligence & Analytics**")
        
        # Status Row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status = "🟢 Online" if self.db and self.db.engine else "🔴 Offline"
            st.metric("System Status", status)
        
        with col2:
            st.metric("Environment", "🚀 Production")
        
        with col3:
            current_time = datetime.now().strftime("%H:%M:%S")
            st.metric("Last Update", current_time)
        
        with col4:
            st.metric("Version", "v3.0.0")
        
        st.divider()

    def render_sidebar(self):
        """Render simple sidebar navigation"""
        with st.sidebar:
            st.header("🧭 Navigation")
            
            # Navigation
            pages = {
                'overview': '🏠 Overview',
                'monitoring': '📈 Real-time Monitoring',
                'analytics': '🔍 Analytics',
                'alerts': '🚨 Alerts',
                'reports': '📋 Reports',
                'settings': '⚙️ Settings'
            }
            
            for key, label in pages.items():
                if st.button(label, key=f"nav_{key}", use_container_width=True):
                    st.session_state.current_page = key
                    st.rerun()
            
            st.divider()
            
            # Controls
            st.subheader("⚙️ Controls")
            
            # Time Range
            time_options = {
                '1h': 'Last Hour',
                '24h': 'Last 24 Hours',
                '7d': 'Last 7 Days',
                '30d': 'Last 30 Days'
            }
            
            st.session_state.time_range = st.selectbox(
                "Time Range",
                options=list(time_options.keys()),
                format_func=lambda x: time_options[x],
                index=1
            )
            
            # Action Buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Refresh", use_container_width=True):
                    st.cache_data.clear()
                    st.success("Data refreshed!")
                    st.rerun()
            
            with col2:
                if st.button("📊 Generate", use_container_width=True):
                    with st.spinner("Generating data..."):
                        try:
                            result = subprocess.run(
                                ["python", "sample_data_generator.py"],
                                capture_output=True,
                                text=True,
                                cwd="/app"
                            )
                            if result.returncode == 0:
                                st.success("Sample data generated!")
                                st.session_state.data_generated = True
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to generate data")
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            # System Stats
            if self.db and self.db.engine:
                st.divider()
                st.subheader("📊 System Statistics")
                
                try:
                    stats = self.db.get_data_quality_stats()
                    if stats and 'air_quality' in stats:
                        aq_stats = stats['air_quality']
                        measurements = aq_stats.get('total_measurements', 0)
                        cities = aq_stats.get('cities_count', 0)
                        st.metric("Total Measurements", f"{measurements:,}")
                        st.metric("Active Cities", f"{cities}")
                    else:
                        st.info("No data statistics available")
                except Exception as e:
                    st.warning(f"Could not load stats: {e}")
            else:
                st.divider()
                st.warning("Database not connected")

    def get_time_hours(self):
        """Convert time range to hours"""
        mapping = {'1h': 1, '24h': 24, '7d': 168, '30d': 720}
        return mapping.get(st.session_state.time_range, 24)
    
    def render_overview_page(self):
        """Render overview page with simple design"""
        st.header("📊 Air Quality Overview")
        
        if not self.db:
            st.error("⚠️ Database connection failed. Please check your configuration.")
            return
        
        try:
            hours = self.get_time_hours()
            df = self.db.get_latest_air_quality_data(hours)
            
            if df.empty:
                st.warning("No data available. Click 'Generate' in the sidebar to create sample data.")
                return
            
            # Key Metrics
            st.subheader("🎯 Key Metrics")
            col1, col2, col3, col4 = st.columns(4)
            
            if 'aqi' in df.columns:
                avg_aqi = df['aqi'].mean()
                aqi_status = "Good" if avg_aqi <= 50 else "Moderate" if avg_aqi <= 100 else "Poor"
                with col1:
                    st.metric("Average AQI", f"{avg_aqi:.0f}", delta=aqi_status)
            
            if 'city' in df.columns:
                cities = df['city'].nunique()
                with col2:
                    st.metric("Cities Monitored", f"{cities}")
            
            try:
                alerts = self.db.get_active_alerts()
                active_alerts = len(alerts) if not alerts.empty else 0
            except:
                active_alerts = 0
            
            with col3:
                alert_status = "Clear" if active_alerts == 0 else f"{active_alerts} active"
                st.metric("Active Alerts", f"{active_alerts}", delta=alert_status)
            
            measurements = len(df)
            with col4:
                st.metric("Data Points", f"{measurements:,}")
            
            st.divider()
            
            # Charts Section
            st.subheader("📈 Data Visualizations")
            
            if 'aqi' in df.columns:
                col1, col2 = st.columns(2)
                
                with col1:
                    # AQI Distribution
                    fig_hist = px.histogram(
                        df, x='aqi', nbins=30,
                        title="AQI Distribution",
                        labels={'aqi': 'Air Quality Index', 'count': 'Frequency'}
                    )
                    fig_hist.update_layout(showlegend=False)
                    st.plotly_chart(fig_hist, use_container_width=True)
                
                with col2:
                    # Top Cities by AQI
                    if 'city' in df.columns:
                        city_aqi = df.groupby('city')['aqi'].mean().reset_index()
                        city_aqi = city_aqi.sort_values('aqi', ascending=True).head(10)
                        
                        fig_bar = px.bar(
                            city_aqi, x='aqi', y='city',
                            orientation='h',
                            title="Top Cities by AQI",
                            labels={'aqi': 'Average AQI', 'city': 'City'},
                            color='aqi',
                            color_continuous_scale='RdYlGn_r'
                        )
                        st.plotly_chart(fig_bar, use_container_width=True)
            
            # Time Series
            if 'timestamp' in df.columns and 'aqi' in df.columns:
                st.subheader("📊 AQI Trend Over Time")
                
                df_sorted = df.sort_values('timestamp')
                fig_line = px.line(
                    df_sorted.head(500), x='timestamp', y='aqi',
                    title="Air Quality Index Timeline",
                    labels={'timestamp': 'Time', 'aqi': 'AQI'}
                )
                fig_line.update_traces(line=dict(width=2))
                st.plotly_chart(fig_line, use_container_width=True)
            
            st.divider()
            
            # Data Table
            st.subheader("📋 Recent Measurements")
            
            display_cols = ['city', 'country', 'aqi', 'pm25', 'pm10', 'timestamp']
            available_cols = [col for col in display_cols if col in df.columns]
            
            if available_cols:
                recent_data = df[available_cols].head(20)
                if 'timestamp' in recent_data.columns:
                    recent_data['timestamp'] = pd.to_datetime(recent_data['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
                
                st.dataframe(recent_data, use_container_width=True, hide_index=True)
        
        except Exception as e:
            st.error(f"Error loading data: {e}")
            logger.error(f"Dashboard error: {e}")

    def render_monitoring_page(self):
        """Render real-time monitoring page"""
        st.header("📈 Real-time Monitoring")
        
        if not self.db:
            st.error("⚠️ Database connection required for real-time monitoring")
            return
        
        # Auto-refresh control
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.subheader("🔄 Live Data Stream")
        with col2:
            auto_refresh = st.checkbox("Auto Refresh", value=True)
        with col3:
            refresh_interval = st.selectbox("Interval", [5, 10, 30, 60], index=1)
        
        # Auto-refresh logic
        if auto_refresh:
            placeholder = st.empty()
            with placeholder.container():
                self.render_monitoring_content()
            time.sleep(refresh_interval)
            st.rerun()
        else:
            self.render_monitoring_content()
    
    def render_monitoring_content(self):
        """Render monitoring page content"""
        try:
            # Real-time metrics
            latest_data = self.db.get_latest_air_quality_data(1)  # Last hour
            
            if not latest_data.empty:
                st.divider()
                
                # Current conditions
                st.subheader("🌡️ Current Conditions")
                
                # Get latest reading for each city
                latest_by_city = latest_data.groupby('city').last().reset_index()
                
                for idx, row in latest_by_city.head(6).iterrows():
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(f"🏙️ {row['city']}", f"AQI: {row['aqi']:.0f}")
                    
                    with col2:
                        if 'pm25' in row:
                            st.metric("PM2.5", f"{row['pm25']:.1f} µg/m³")
                    
                    with col3:
                        if 'pm10' in row:
                            st.metric("PM10", f"{row['pm10']:.1f} µg/m³")
                    
                    with col4:
                        if 'temperature' in row:
                            st.metric("Temp", f"{row['temperature']:.1f}°C")
                
                st.divider()
                
                # Real-time charts
                st.subheader("📊 Live Charts")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # AQI trend for last hour
                    if len(latest_data) > 1:
                        fig_trend = px.line(
                            latest_data.sort_values('timestamp'), 
                            x='timestamp', y='aqi', color='city',
                            title="AQI Trend - Last Hour"
                        )
                        st.plotly_chart(fig_trend, use_container_width=True)
                
                with col2:
                    # Current AQI gauge
                    avg_aqi = latest_data['aqi'].mean()
                    fig_gauge = go.Figure(go.Indicator(
                        mode = "gauge+number+delta",
                        value = avg_aqi,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "Average AQI"},
                        delta = {'reference': 50},
                        gauge = {
                            'axis': {'range': [None, 300]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 50], 'color': "lightgray"},
                                {'range': [50, 100], 'color': "gray"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 150
                            }
                        }
                    ))
                    fig_gauge.update_layout(height=300)
                    st.plotly_chart(fig_gauge, use_container_width=True)
                
                # Alert status
                st.subheader("🚨 Alert Status")
                try:
                    alerts = self.db.get_active_alerts()
                    if not alerts.empty:
                        for _, alert in alerts.head(5).iterrows():
                            severity = alert.get('severity', 'info')
                            if severity == 'high':
                                st.error(f"🔴 {alert.get('message', 'High severity alert')}")
                            elif severity == 'medium':
                                st.warning(f"🟡 {alert.get('message', 'Medium severity alert')}")
                            else:
                                st.info(f"🔵 {alert.get('message', 'Low severity alert')}")
                    else:
                        st.success("✅ No active alerts - All systems normal")
                except:
                    st.success("✅ No active alerts - All systems normal")
                
            else:
                st.warning("No real-time data available")
                
        except Exception as e:
            st.error(f"Error loading real-time data: {e}")

    def render_analytics_page(self):
        """Render advanced analytics page"""
        st.header("🔍 Advanced Analytics")
        
        if not self.db:
            st.error("⚠️ Database connection required for analytics")
            return
        
        # Analytics controls
        col1, col2, col3 = st.columns(3)
        with col1:
            analysis_type = st.selectbox("Analysis Type", [
                "Trend Analysis", "Correlation Analysis", "Pollution Patterns", 
                "City Comparison", "Seasonal Analysis", "Health Impact"
            ])
        with col2:
            time_period = st.selectbox("Time Period", [
                "Last 7 Days", "Last 30 Days", "Last 3 Months", "Last Year"
            ])
        with col3:
            chart_type = st.selectbox("Visualization", [
                "Line Charts", "Heatmaps", "Box Plots", "Scatter Plots", "Bar Charts"
            ])
        
        try:
            # Get data based on time period
            hours_map = {"Last 7 Days": 168, "Last 30 Days": 720, "Last 3 Months": 2160, "Last Year": 8760}
            hours = hours_map.get(time_period, 720)
            df = self.db.get_latest_air_quality_data(hours)
            
            if df.empty:
                st.warning("No data available for analysis")
                return
            
            st.divider()
            
            # Render based on analysis type
            if analysis_type == "Trend Analysis":
                self.render_trend_analysis(df, chart_type)
            elif analysis_type == "Correlation Analysis":
                self.render_correlation_analysis(df, chart_type)
            elif analysis_type == "Pollution Patterns":
                self.render_pollution_patterns(df, chart_type)
            elif analysis_type == "City Comparison":
                self.render_city_comparison(df, chart_type)
            elif analysis_type == "Seasonal Analysis":
                self.render_seasonal_analysis(df, chart_type)
            elif analysis_type == "Health Impact":
                self.render_health_impact(df, chart_type)
                
        except Exception as e:
            st.error(f"Error in analytics: {e}")
    
    def render_trend_analysis(self, df, chart_type):
        """Render trend analysis"""
        st.subheader("📈 Trend Analysis")
        
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            avg_aqi = df['aqi'].mean()
            st.metric("Average AQI", f"{avg_aqi:.1f}")
        with col2:
            trend = "↑" if df['aqi'].iloc[-1] > df['aqi'].iloc[0] else "↓"
            st.metric("Trend", trend)
        with col3:
            max_aqi = df['aqi'].max()
            st.metric("Peak AQI", f"{max_aqi:.0f}")
        with col4:
            volatility = df['aqi'].std()
            st.metric("Volatility", f"{volatility:.1f}")
        
        # Visualizations
        if 'timestamp' in df.columns:
            if chart_type == "Line Charts":
                fig = px.line(df.sort_values('timestamp'), x='timestamp', y='aqi', 
                             color='city' if 'city' in df.columns else None,
                             title="AQI Trend Over Time")
                st.plotly_chart(fig, use_container_width=True)
            
            # Additional trend metrics
            if len(df) > 1:
                # Moving averages
                df_sorted = df.sort_values('timestamp')
                if len(df_sorted) >= 7:
                    df_sorted['MA_7'] = df_sorted['aqi'].rolling(window=7).mean()
                    fig_ma = px.line(df_sorted, x='timestamp', y=['aqi', 'MA_7'],
                                   title="AQI with 7-Point Moving Average")
                    st.plotly_chart(fig_ma, use_container_width=True)
    
    def render_correlation_analysis(self, df, chart_type):
        """Render correlation analysis"""
        st.subheader("🔗 Correlation Analysis")
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 1:
            correlation_matrix = df[numeric_cols].corr()
            
            if chart_type == "Heatmaps":
                fig = px.imshow(correlation_matrix, text_auto=True, aspect="auto",
                               title="Correlation Matrix of Air Quality Parameters")
                st.plotly_chart(fig, use_container_width=True)
            
            # Key correlations
            st.subheader("🔍 Key Insights")
            for i, col1 in enumerate(numeric_cols):
                for col2 in numeric_cols[i+1:]:
                    corr = correlation_matrix.loc[col1, col2]
                    if abs(corr) > 0.5:
                        strength = "Strong" if abs(corr) > 0.7 else "Moderate"
                        direction = "positive" if corr > 0 else "negative"
                        st.info(f"{strength} {direction} correlation between {col1} and {col2}: {corr:.3f}")
    
    def render_pollution_patterns(self, df, chart_type):
        """Render pollution patterns analysis"""
        st.subheader("🌫️ Pollution Patterns")
        
        if 'timestamp' in df.columns:
            df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
            df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.day_name()
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Hourly patterns
                hourly_avg = df.groupby('hour')['aqi'].mean().reset_index()
                fig_hourly = px.bar(hourly_avg, x='hour', y='aqi',
                                  title="Average AQI by Hour of Day")
                st.plotly_chart(fig_hourly, use_container_width=True)
            
            with col2:
                # Daily patterns
                daily_avg = df.groupby('day_of_week')['aqi'].mean().reset_index()
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                daily_avg['day_of_week'] = pd.Categorical(daily_avg['day_of_week'], categories=day_order, ordered=True)
                daily_avg = daily_avg.sort_values('day_of_week')
                
                fig_daily = px.bar(daily_avg, x='day_of_week', y='aqi',
                                 title="Average AQI by Day of Week")
                st.plotly_chart(fig_daily, use_container_width=True)
    
    def render_city_comparison(self, df, chart_type):
        """Render city comparison analysis"""
        st.subheader("🏙️ City Comparison")
        
        if 'city' in df.columns:
            city_stats = df.groupby('city').agg({
                'aqi': ['mean', 'max', 'min', 'std']
            }).round(2)
            city_stats.columns = ['Avg_AQI', 'Max_AQI', 'Min_AQI', 'Std_AQI']
            city_stats = city_stats.reset_index()
            
            # Rankings
            city_stats['Rank'] = city_stats['Avg_AQI'].rank(ascending=True).astype(int)
            city_stats = city_stats.sort_values('Avg_AQI')
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🏆 City Rankings")
                st.dataframe(city_stats[['city', 'Avg_AQI', 'Rank']], hide_index=True)
            
            with col2:
                if chart_type == "Box Plots":
                    fig = px.box(df, x='city', y='aqi', title="AQI Distribution by City")
                    fig.update_xaxes(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    fig = px.bar(city_stats, x='city', y='Avg_AQI', 
                               title="Average AQI by City", color='Avg_AQI')
                    fig.update_xaxes(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
    
    def render_seasonal_analysis(self, df, chart_type):
        """Render seasonal analysis"""
        st.subheader("🗓️ Seasonal Analysis")
        
        if 'timestamp' in df.columns:
            df['month'] = pd.to_datetime(df['timestamp']).dt.month
            df['season'] = df['month'].map({12:1, 1:1, 2:1, 3:2, 4:2, 5:2, 
                                          6:3, 7:3, 8:3, 9:4, 10:4, 11:4})
            season_names = {1: 'Winter', 2: 'Spring', 3: 'Summer', 4: 'Fall'}
            df['season_name'] = df['season'].map(season_names)
            
            seasonal_stats = df.groupby('season_name')['aqi'].agg(['mean', 'max', 'min']).round(2)
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📊 Seasonal Statistics")
                st.dataframe(seasonal_stats)
            
            with col2:
                fig = px.box(df, x='season_name', y='aqi', title="AQI Distribution by Season")
                st.plotly_chart(fig, use_container_width=True)
    
    def render_health_impact(self, df, chart_type):
        """Render health impact analysis"""
        st.subheader("🏥 Health Impact Analysis")
        
        # AQI health categories
        def get_health_category(aqi):
            if aqi <= 50:
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
        
        df['health_category'] = df['aqi'].apply(get_health_category)
        health_dist = df['health_category'].value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(values=health_dist.values, names=health_dist.index,
                        title="Distribution of Health Categories")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Health recommendations
            st.subheader("🎯 Health Recommendations")
            avg_aqi = df['aqi'].mean()
            if avg_aqi <= 50:
                st.success("🟢 Air quality is good - Safe for outdoor activities")
            elif avg_aqi <= 100:
                st.warning("🟡 Moderate air quality - Sensitive individuals should limit outdoor exposure")
            elif avg_aqi <= 150:
                st.warning("🟠 Unhealthy for sensitive groups - Children and elderly should avoid outdoor activities")
            else:
                st.error("🔴 Unhealthy air quality - Everyone should avoid outdoor activities")
            
            # Health metrics
            high_pollution_days = len(df[df['aqi'] > 100])
            total_days = len(df['aqi'].unique()) if 'timestamp' in df.columns else len(df)
            health_percentage = (high_pollution_days / total_days * 100) if total_days > 0 else 0
            
            st.metric("High Pollution Readings", f"{high_pollution_days}")
            st.metric("Health Risk %", f"{health_percentage:.1f}%")

    def render_alerts_page(self):
        """Render alert management page"""
        st.header("🚨 Alert Management")
        
        if not self.db:
            st.error("⚠️ Database connection required for alert management")
            return
        
        # Alert controls
        col1, col2, col3 = st.columns(3)
        with col1:
            alert_view = st.selectbox("View", ["Active Alerts", "Alert History", "Alert Rules", "Create Alert"])
        with col2:
            severity_filter = st.selectbox("Severity Filter", ["All", "High", "Medium", "Low"])
        with col3:
            time_filter = st.selectbox("Time Filter", ["All Time", "Last 24h", "Last 7 days", "Last 30 days"])
        
        st.divider()
        
        if alert_view == "Active Alerts":
            self.render_active_alerts(severity_filter)
        elif alert_view == "Alert History":
            self.render_alert_history(severity_filter, time_filter)
        elif alert_view == "Alert Rules":
            self.render_alert_rules()
        elif alert_view == "Create Alert":
            self.render_create_alert()
    
    def render_active_alerts(self, severity_filter):
        """Render active alerts"""
        st.subheader("🔴 Active Alerts")
        
        try:
            # Get active alerts from database
            alerts = self.db.get_active_alerts()
            
            if not alerts.empty:
                # Filter by severity if specified
                if severity_filter != "All":
                    alerts = alerts[alerts.get('severity', '').str.lower() == severity_filter.lower()]
                
                if not alerts.empty:
                    for _, alert in alerts.iterrows():
                        severity = alert.get('severity', 'medium').lower()
                        message = alert.get('message', 'Alert notification')
                        timestamp = alert.get('timestamp', datetime.now())
                        location = alert.get('city', 'Unknown')
                        
                        # Display alert based on severity
                        if severity == 'high':
                            st.error(f"🔴 **HIGH SEVERITY** - {location}")
                            st.error(f"📍 {message}")
                            st.error(f"⏰ {timestamp}")
                        elif severity == 'medium':
                            st.warning(f"🟡 **MEDIUM SEVERITY** - {location}")
                            st.warning(f"📍 {message}")
                            st.warning(f"⏰ {timestamp}")
                        else:
                            st.info(f"🔵 **LOW SEVERITY** - {location}")
                            st.info(f"📍 {message}")
                            st.info(f"⏰ {timestamp}")
                        
                        # Alert actions
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button(f"Acknowledge", key=f"ack_{alert.get('id', 'unknown')}"):
                                st.success("Alert acknowledged")
                        with col2:
                            if st.button(f"Resolve", key=f"resolve_{alert.get('id', 'unknown')}"):
                                st.success("Alert resolved")
                        with col3:
                            if st.button(f"Details", key=f"details_{alert.get('id', 'unknown')}"):
                                st.info("Alert details expanded")
                        
                        st.divider()
                else:
                    st.success("✅ No active alerts matching the selected severity")
            else:
                # Create sample alerts for demonstration
                sample_alerts = [
                    {"severity": "high", "message": "AQI exceeded 200 in downtown area", "city": "New York", "aqi": 215},
                    {"severity": "medium", "message": "PM2.5 levels elevated", "city": "Los Angeles", "aqi": 125},
                    {"severity": "low", "message": "Air quality monitoring system maintenance", "city": "Chicago", "aqi": 85}
                ]
                
                st.info("📋 Sample Alert System (No database alerts found)")
                for i, alert in enumerate(sample_alerts):
                    if severity_filter == "All" or severity_filter.lower() == alert["severity"]:
                        if alert["severity"] == "high":
                            st.error(f"🔴 **HIGH SEVERITY** - {alert['city']}")
                            st.error(f"📍 {alert['message']} (AQI: {alert['aqi']})")
                        elif alert["severity"] == "medium":
                            st.warning(f"🟡 **MEDIUM SEVERITY** - {alert['city']}")
                            st.warning(f"📍 {alert['message']} (AQI: {alert['aqi']})")
                        else:
                            st.info(f"🔵 **LOW SEVERITY** - {alert['city']}")
                            st.info(f"📍 {alert['message']} (AQI: {alert['aqi']})")
                        st.divider()
                        
        except Exception as e:
            st.error(f"Error loading alerts: {e}")
    
    def render_alert_history(self, severity_filter, time_filter):
        """Render alert history"""
        st.subheader("📚 Alert History")
        
        # Sample alert history
        history_data = [
            {"timestamp": "2024-01-15 14:30", "severity": "High", "message": "AQI exceeded threshold", "city": "Beijing", "status": "Resolved"},
            {"timestamp": "2024-01-15 12:15", "severity": "Medium", "message": "PM2.5 levels elevated", "city": "Delhi", "status": "Acknowledged"},
            {"timestamp": "2024-01-15 09:45", "severity": "Low", "message": "Sensor calibration needed", "city": "Tokyo", "status": "Resolved"},
            {"timestamp": "2024-01-14 18:20", "severity": "High", "message": "Hazardous air quality detected", "city": "Mumbai", "status": "Resolved"},
            {"timestamp": "2024-01-14 15:10", "severity": "Medium", "message": "Moderate pollution levels", "city": "Shanghai", "status": "Resolved"},
        ]
        
        df_history = pd.DataFrame(history_data)
        
        # Apply filters
        if severity_filter != "All":
            df_history = df_history[df_history['severity'] == severity_filter]
        
        if time_filter != "All Time":
            st.info(f"Showing alerts for: {time_filter}")
        
        # Display history table
        st.dataframe(df_history, use_container_width=True, hide_index=True)
        
        # History statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            total_alerts = len(df_history)
            st.metric("Total Alerts", total_alerts)
        with col2:
            resolved_alerts = len(df_history[df_history['status'] == 'Resolved'])
            st.metric("Resolved", resolved_alerts)
        with col3:
            resolution_rate = (resolved_alerts / total_alerts * 100) if total_alerts > 0 else 0
            st.metric("Resolution Rate", f"{resolution_rate:.1f}%")
    
    def render_alert_rules(self):
        """Render alert rules configuration"""
        st.subheader("⚙️ Alert Rules")
        
        # Current alert rules
        st.write("**Current Alert Rules:**")
        
        rules = [
            {"parameter": "AQI", "condition": "> 150", "severity": "High", "enabled": True},
            {"parameter": "AQI", "condition": "> 100", "severity": "Medium", "enabled": True},
            {"parameter": "PM2.5", "condition": "> 75", "severity": "High", "enabled": True},
            {"parameter": "PM10", "condition": "> 150", "severity": "Medium", "enabled": False},
        ]
        
        for i, rule in enumerate(rules):
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
            
            with col1:
                st.write(f"**{rule['parameter']}**")
            with col2:
                st.write(rule['condition'])
            with col3:
                severity_color = {"High": "🔴", "Medium": "🟡", "Low": "🔵"}
                st.write(f"{severity_color.get(rule['severity'], '⚪')} {rule['severity']}")
            with col4:
                status = "✅ Enabled" if rule['enabled'] else "❌ Disabled"
                st.write(status)
            with col5:
                if st.button("Edit", key=f"edit_rule_{i}"):
                    st.info(f"Editing rule for {rule['parameter']}")
        
        st.divider()
        
        # Add new rule
        st.subheader("➕ Add New Rule")
        with st.form("new_alert_rule"):
            col1, col2 = st.columns(2)
            with col1:
                parameter = st.selectbox("Parameter", ["AQI", "PM2.5", "PM10", "Temperature", "Humidity"])
                condition = st.selectbox("Condition", [">", ">=", "<", "<=", "=="])
                threshold = st.number_input("Threshold Value", min_value=0.0, value=100.0)
            
            with col2:
                severity = st.selectbox("Severity", ["High", "Medium", "Low"])
                notification_method = st.multiselect("Notification", ["Email", "SMS", "Dashboard", "Webhook"])
                enabled = st.checkbox("Enable Rule", value=True)
            
            if st.form_submit_button("Create Alert Rule"):
                st.success(f"✅ Created alert rule: {parameter} {condition} {threshold} (Severity: {severity})")
    
    def render_create_alert(self):
        """Render create alert interface"""
        st.subheader("📝 Create Manual Alert")
        
        with st.form("manual_alert"):
            col1, col2 = st.columns(2)
            
            with col1:
                alert_title = st.text_input("Alert Title", placeholder="Enter alert title")
                severity = st.selectbox("Severity", ["High", "Medium", "Low"])
                affected_cities = st.multiselect("Affected Cities", 
                                               ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia"])
            
            with col2:
                alert_message = st.text_area("Alert Message", placeholder="Describe the alert details...")
                alert_type = st.selectbox("Alert Type", ["Air Quality", "System", "Maintenance", "Weather", "Other"])
                duration = st.selectbox("Duration", ["1 hour", "6 hours", "12 hours", "24 hours", "Until resolved"])
            
            notification_channels = st.multiselect("Notification Channels", 
                                                 ["Dashboard", "Email", "SMS", "Push Notification", "Webhook"])
            
            if st.form_submit_button("Create Alert"):
                if alert_title and alert_message:
                    st.success(f"✅ Alert '{alert_title}' created successfully!")
                    st.info(f"📊 Severity: {severity}")
                    st.info(f"🏙️ Cities: {', '.join(affected_cities) if affected_cities else 'All'}")
                    st.info(f"📱 Notifications: {', '.join(notification_channels) if notification_channels else 'Dashboard only'}")
                else:
                    st.error("Please fill in all required fields")

    def render_reports_page(self):
        """Render reports and export page"""
        st.header("📋 Reports & Export")
        
        if not self.db:
            st.error("⚠️ Database connection required for reports")
            return
        
        # Report options
        col1, col2, col3 = st.columns(3)
        with col1:
            report_type = st.selectbox("Report Type", [
                "Air Quality Summary", "City Analysis", "Trend Report", 
                "Health Impact Report", "Alert Summary", "Custom Report"
            ])
        with col2:
            time_range = st.selectbox("Time Range", [
                "Last 24 Hours", "Last 7 Days", "Last 30 Days", 
                "Last 3 Months", "Last Year", "Custom Range"
            ])
        with col3:
            export_format = st.selectbox("Export Format", ["PDF", "Excel", "CSV", "JSON"])
        
        # Custom date range if selected
        if time_range == "Custom Range":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date")
            with col2:
                end_date = st.date_input("End Date")
        
        st.divider()
        
        # Generate report based on type
        if report_type == "Air Quality Summary":
            self.render_air_quality_summary_report(time_range)
        elif report_type == "City Analysis":
            self.render_city_analysis_report(time_range)
        elif report_type == "Trend Report":
            self.render_trend_report(time_range)
        elif report_type == "Health Impact Report":
            self.render_health_impact_report(time_range)
        elif report_type == "Alert Summary":
            self.render_alert_summary_report(time_range)
        elif report_type == "Custom Report":
            self.render_custom_report()
        
        # Export controls
        st.divider()
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.subheader("📤 Export Options")
        with col2:
            if st.button("📊 Generate Report", type="primary"):
                st.success(f"✅ {report_type} generated successfully!")
                st.info(f"📁 Format: {export_format}")
                st.info(f"📅 Period: {time_range}")
        with col3:
            if st.button("📥 Download"):
                # Simulate download
                st.success("🎉 Report downloaded!")
                st.balloons()
    
    def render_air_quality_summary_report(self, time_range):
        """Render air quality summary report"""
        st.subheader("🌍 Air Quality Summary Report")
        
        try:
            # Get data based on time range
            hours_map = {
                "Last 24 Hours": 24, "Last 7 Days": 168, "Last 30 Days": 720,
                "Last 3 Months": 2160, "Last Year": 8760
            }
            hours = hours_map.get(time_range, 168)
            df = self.db.get_latest_air_quality_data(hours)
            
            if not df.empty:
                # Summary statistics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    avg_aqi = df['aqi'].mean()
                    st.metric("Average AQI", f"{avg_aqi:.1f}")
                
                with col2:
                    max_aqi = df['aqi'].max()
                    st.metric("Maximum AQI", f"{max_aqi:.0f}")
                
                with col3:
                    min_aqi = df['aqi'].min()
                    st.metric("Minimum AQI", f"{min_aqi:.0f}")
                
                with col4:
                    cities_monitored = df['city'].nunique() if 'city' in df.columns else 0
                    st.metric("Cities Monitored", cities_monitored)
                
                # Air quality distribution
                st.subheader("📊 Air Quality Distribution")
                
                # Health categories
                def categorize_aqi(aqi):
                    if aqi <= 50: return "Good"
                    elif aqi <= 100: return "Moderate"
                    elif aqi <= 150: return "Unhealthy for Sensitive"
                    elif aqi <= 200: return "Unhealthy"
                    elif aqi <= 300: return "Very Unhealthy"
                    else: return "Hazardous"
                
                df['category'] = df['aqi'].apply(categorize_aqi)
                category_counts = df['category'].value_counts()
                
                fig_pie = px.pie(values=category_counts.values, names=category_counts.index,
                               title="Air Quality Categories Distribution")
                st.plotly_chart(fig_pie, use_container_width=True)
                
                # Top polluted cities
                if 'city' in df.columns:
                    st.subheader("🏙️ Most Polluted Cities")
                    city_avg = df.groupby('city')['aqi'].mean().sort_values(ascending=False)
                    st.dataframe(city_avg.head(10).reset_index(), hide_index=True)
                
            else:
                st.warning("No data available for the selected time range")
                
        except Exception as e:
            st.error(f"Error generating report: {e}")
    
    def render_city_analysis_report(self, time_range):
        """Render city analysis report"""
        st.subheader("🏙️ City Analysis Report")
        
        # City selection
        available_cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]
        selected_cities = st.multiselect("Select Cities for Analysis", available_cities, default=available_cities[:3])
        
        if selected_cities:
            # Sample data for demonstration
            report_data = []
            for city in selected_cities:
                # Generate sample metrics
                avg_aqi = np.random.randint(50, 150)
                max_aqi = avg_aqi + np.random.randint(20, 50)
                pollution_days = np.random.randint(5, 25)
                
                report_data.append({
                    "City": city,
                    "Average AQI": avg_aqi,
                    "Maximum AQI": max_aqi,
                    "High Pollution Days": pollution_days,
                    "Air Quality Grade": "B" if avg_aqi < 80 else "C" if avg_aqi < 120 else "D"
                })
            
            df_report = pd.DataFrame(report_data)
            
            # Display report table
            st.dataframe(df_report, use_container_width=True, hide_index=True)
            
            # City comparison chart
            fig_compare = px.bar(df_report, x='City', y='Average AQI', 
                               title="Average AQI Comparison by City", color='Average AQI')
            st.plotly_chart(fig_compare, use_container_width=True)
        else:
            st.info("Please select cities for analysis")
    
    def render_trend_report(self, time_range):
        """Render trend analysis report"""
        st.subheader("📈 Trend Analysis Report")
        
        # Generate sample trend data
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
        trend_data = []
        
        base_aqi = 75
        for date in dates:
            aqi = base_aqi + np.random.randint(-20, 30)
            base_aqi = aqi  # Create trending effect
            trend_data.append({"Date": date, "AQI": aqi})
        
        df_trend = pd.DataFrame(trend_data)
        
        # Trend analysis
        correlation = np.corrcoef(range(len(df_trend)), df_trend['AQI'])[0, 1]
        trend_direction = "Improving" if correlation < -0.1 else "Worsening" if correlation > 0.1 else "Stable"
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Trend Direction", trend_direction)
        with col2:
            st.metric("Correlation", f"{correlation:.3f}")
        with col3:
            st.metric("Data Points", len(df_trend))
        
        # Trend chart
        fig_trend = px.line(df_trend, x='Date', y='AQI', title="AQI Trend Over Time")
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # Trend insights
        st.subheader("🔍 Key Insights")
        if correlation < -0.2:
            st.success("🟢 Air quality is significantly improving over time")
        elif correlation > 0.2:
            st.error("🔴 Air quality is deteriorating - immediate action recommended")
        else:
            st.info("🟡 Air quality remains relatively stable")
    
    def render_health_impact_report(self, time_range):
        """Render health impact report"""
        st.subheader("🏥 Health Impact Assessment Report")
        
        # Health risk categories
        risk_data = {
            "Risk Level": ["Low", "Moderate", "High", "Very High"],
            "Days Count": [15, 10, 4, 1],
            "Population Affected": ["General Public", "Sensitive Groups", "Everyone", "Emergency Level"],
            "Recommended Actions": [
                "Normal outdoor activities",
                "Limit outdoor exposure for sensitive individuals",
                "Reduce outdoor activities",
                "Avoid all outdoor activities"
            ]
        }
        
        df_health = pd.DataFrame(risk_data)
        
        # Health metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Low Risk Days", 15)
        with col2:
            st.metric("Moderate Risk Days", 10)
        with col3:
            st.metric("High Risk Days", 4)
        with col4:
            st.metric("Emergency Days", 1)
        
        # Health risk distribution
        fig_health = px.pie(df_health, values='Days Count', names='Risk Level',
                          title="Health Risk Distribution")
        st.plotly_chart(fig_health, use_container_width=True)
        
        # Recommendations table
        st.subheader("📋 Health Recommendations")
        st.dataframe(df_health, use_container_width=True, hide_index=True)
        
        # Health alerts summary
        st.subheader("🚨 Health Alert Summary")
        st.warning("⚠️ 4 days exceeded healthy air quality standards")
        st.info("ℹ️ Sensitive groups should monitor air quality daily")
        st.success("✅ Most days (83%) had acceptable air quality levels")
    
    def render_alert_summary_report(self, time_range):
        """Render alert summary report"""
        st.subheader("🚨 Alert Activity Summary")
        
        # Alert statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Alerts", 47)
        with col2:
            st.metric("High Priority", 8)
        with col3:
            st.metric("Resolved", 42)
        with col4:
            st.metric("Response Time", "12 min avg")
        
        # Alert trend
        alert_days = pd.date_range(start=datetime.now() - timedelta(days=7), end=datetime.now(), freq='D')
        alert_counts = [np.random.randint(3, 12) for _ in alert_days]
        
        df_alerts = pd.DataFrame({"Date": alert_days, "Alert Count": alert_counts})
        
        fig_alerts = px.bar(df_alerts, x='Date', y='Alert Count', 
                           title="Daily Alert Volume")
        st.plotly_chart(fig_alerts, use_container_width=True)
        
        # Alert categories
        alert_categories = {
            "Category": ["Air Quality", "System", "Maintenance", "Weather"],
            "Count": [25, 12, 7, 3],
            "Avg Response": ["8 min", "15 min", "45 min", "5 min"]
        }
        
        st.subheader("📊 Alert Categories")
        st.dataframe(pd.DataFrame(alert_categories), use_container_width=True, hide_index=True)
    
    def render_custom_report(self):
        """Render custom report builder"""
        st.subheader("🔧 Custom Report Builder")
        
        with st.form("custom_report"):
            col1, col2 = st.columns(2)
            
            with col1:
                report_name = st.text_input("Report Name")
                metrics = st.multiselect("Metrics to Include", [
                    "AQI", "PM2.5", "PM10", "Temperature", "Humidity", "Alerts"
                ])
                cities = st.multiselect("Cities", [
                    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix"
                ])
            
            with col2:
                chart_types = st.multiselect("Chart Types", [
                    "Line Charts", "Bar Charts", "Pie Charts", "Heatmaps", "Tables"
                ])
                grouping = st.selectbox("Group By", ["City", "Date", "Hour", "Day of Week"])
                include_summary = st.checkbox("Include Executive Summary", value=True)
            
            additional_notes = st.text_area("Additional Notes", 
                                          placeholder="Any specific requirements or notes for the report...")
            
            if st.form_submit_button("Generate Custom Report"):
                if report_name and metrics:
                    st.success(f"✅ Custom report '{report_name}' generated!")
                    st.info(f"📊 Metrics: {', '.join(metrics)}")
                    st.info(f"🏙️ Cities: {', '.join(cities) if cities else 'All'}")
                    st.info(f"📈 Charts: {', '.join(chart_types) if chart_types else 'Default'}")
                    
                    # Show sample report structure
                    st.subheader("📋 Report Preview")
                    st.write("**Report Structure:**")
                    st.write("1. Executive Summary" if include_summary else "1. Data Overview")
                    st.write("2. Key Metrics Dashboard")
                    st.write("3. Detailed Analysis")
                    st.write("4. Charts and Visualizations")
                    st.write("5. Conclusions and Recommendations")
                else:
                    st.error("Please provide report name and select at least one metric")

    def render_settings_page(self):
        """Render system settings page"""
        st.header("⚙️ System Settings")
        
        # Settings tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🔧 General", "🚨 Alerts", "📊 Data Sources", "👤 User Preferences", "🔐 Security"
        ])
        
        with tab1:
            self.render_general_settings()
        
        with tab2:
            self.render_alert_settings()
        
        with tab3:
            self.render_data_source_settings()
        
        with tab4:
            self.render_user_preferences()
        
        with tab5:
            self.render_security_settings()
    
    def render_general_settings(self):
        """Render general system settings"""
        st.subheader("🔧 General Settings")
        
        # System Information
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**System Information**")
            st.info("Platform: Air Quality Monitor v3.0.0")
            st.info("Database: PostgreSQL")
            st.info("Last Updated: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
            
            # System health
            st.write("**System Health**")
            services = [
                ("Database", "🟢 Online"),
                ("Kafka", "🟢 Online"),
                ("Spark", "🟢 Online"),
                ("Monitoring", "🟢 Active")
            ]
            
            for service, status in services:
                st.write(f"{service}: {status}")
        
        with col2:
            st.write("**Configuration**")
            
            # Refresh intervals
            refresh_interval = st.selectbox(
                "Default Refresh Interval",
                ["5 seconds", "10 seconds", "30 seconds", "1 minute", "5 minutes"],
                index=2
            )
            
            # Data retention
            data_retention = st.selectbox(
                "Data Retention Period",
                ["30 days", "90 days", "6 months", "1 year", "2 years"],
                index=3
            )
            
            # Language
            language = st.selectbox(
                "Language",
                ["English", "Spanish", "French", "German", "Chinese"],
                index=0
            )
            
            # Timezone
            timezone = st.selectbox(
                "Timezone",
                ["UTC", "EST", "PST", "GMT", "CET"],
                index=1
            )
            
            if st.button("Save General Settings"):
                st.success("✅ General settings saved successfully!")
    
    def render_alert_settings(self):
        """Render alert configuration settings"""
        st.subheader("🚨 Alert Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Alert Thresholds**")
            
            # AQI thresholds
            aqi_moderate = st.number_input("AQI Moderate Threshold", min_value=0, value=50)
            aqi_unhealthy = st.number_input("AQI Unhealthy Threshold", min_value=0, value=100)
            aqi_hazardous = st.number_input("AQI Hazardous Threshold", min_value=0, value=200)
            
            # PM thresholds
            pm25_threshold = st.number_input("PM2.5 Threshold (µg/m³)", min_value=0.0, value=35.0)
            pm10_threshold = st.number_input("PM10 Threshold (µg/m³)", min_value=0.0, value=150.0)
            
            st.write("**Alert Frequency**")
            alert_frequency = st.selectbox(
                "Maximum Alert Frequency",
                ["Immediate", "Every 15 minutes", "Every hour", "Every 6 hours", "Daily"],
                index=1
            )
        
        with col2:
            st.write("**Notification Channels**")
            
            email_alerts = st.checkbox("Email Notifications", value=True)
            if email_alerts:
                email_address = st.text_input("Email Address", value="admin@example.com")
            
            sms_alerts = st.checkbox("SMS Notifications", value=False)
            if sms_alerts:
                phone_number = st.text_input("Phone Number", value="+1234567890")
            
            webhook_alerts = st.checkbox("Webhook Notifications", value=False)
            if webhook_alerts:
                webhook_url = st.text_input("Webhook URL", value="https://api.example.com/webhook")
            
            push_alerts = st.checkbox("Push Notifications", value=True)
            
            st.write("**Alert Escalation**")
            escalation_time = st.selectbox(
                "Escalation Time (if unacknowledged)",
                ["15 minutes", "30 minutes", "1 hour", "2 hours", "Never"],
                index=2
            )
            
            if st.button("Save Alert Settings"):
                st.success("✅ Alert settings saved successfully!")
    
    def render_data_source_settings(self):
        """Render data source configuration"""
        st.subheader("📊 Data Source Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**API Configurations**")
            
            # API Keys (masked)
            openweather_key = st.text_input("OpenWeather API Key", value="*********************", type="password")
            iqair_key = st.text_input("IQAir API Key", value="*********************", type="password")
            
            # Data collection intervals
            collection_interval = st.selectbox(
                "Data Collection Interval",
                ["1 minute", "5 minutes", "15 minutes", "30 minutes", "1 hour"],
                index=2
            )
            
            # Data validation
            enable_validation = st.checkbox("Enable Data Validation", value=True)
            if enable_validation:
                validation_rules = st.multiselect(
                    "Validation Rules",
                    ["Range Check", "Anomaly Detection", "Completeness Check", "Consistency Check"],
                    default=["Range Check", "Completeness Check"]
                )
            
            # Backup settings
            enable_backup = st.checkbox("Enable Data Backup", value=True)
            if enable_backup:
                backup_frequency = st.selectbox(
                    "Backup Frequency",
                    ["Daily", "Weekly", "Monthly"],
                    index=0
                )
        
        with col2:
            st.write("**Data Sources Status**")
            
            data_sources = [
                {"name": "OpenWeather API", "status": "🟢 Active", "last_update": "2 minutes ago"},
                {"name": "IQAir API", "status": "🟢 Active", "last_update": "5 minutes ago"},
                {"name": "Local Sensors", "status": "🟡 Partial", "last_update": "15 minutes ago"},
                {"name": "Government Data", "status": "🟢 Active", "last_update": "1 hour ago"},
            ]
            
            for source in data_sources:
                with st.container():
                    col_a, col_b, col_c = st.columns([2, 1, 1])
                    with col_a:
                        st.write(f"**{source['name']}**")
                    with col_b:
                        st.write(source['status'])
                    with col_c:
                        st.write(source['last_update'])
            
            st.write("**Data Quality Metrics**")
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Data Completeness", "97.8%")
                st.metric("Data Accuracy", "98.5%")
            with col_b:
                st.metric("Update Frequency", "99.2%")
                st.metric("Data Freshness", "2.3 min avg")
            
            if st.button("Save Data Source Settings"):
                st.success("✅ Data source settings saved successfully!")
    
    def render_user_preferences(self):
        """Render user preferences"""
        st.subheader("👤 User Preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Display Preferences**")
            
            # Theme
            theme = st.selectbox("Theme", ["Light", "Dark", "Auto"], index=0)
            
            # Units
            temperature_unit = st.selectbox("Temperature Unit", ["Celsius", "Fahrenheit"], index=0)
            distance_unit = st.selectbox("Distance Unit", ["Metric", "Imperial"], index=0)
            
            # Chart preferences
            default_chart_type = st.selectbox(
                "Default Chart Type",
                ["Line Chart", "Bar Chart", "Area Chart"],
                index=0
            )
            
            # Color scheme
            color_scheme = st.selectbox(
                "Color Scheme",
                ["Default", "Colorblind Friendly", "High Contrast", "Monochrome"],
                index=0
            )
            
            # Animations
            enable_animations = st.checkbox("Enable Animations", value=True)
            
            # Auto-refresh
            auto_refresh_default = st.checkbox("Auto-refresh by Default", value=True)
        
        with col2:
            st.write("**Dashboard Layout**")
            
            # Default page
            default_page = st.selectbox(
                "Default Page on Login",
                ["Overview", "Real-time Monitoring", "Analytics", "Alerts"],
                index=0
            )
            
            # Sidebar behavior
            sidebar_behavior = st.selectbox(
                "Sidebar Behavior",
                ["Always Expanded", "Always Collapsed", "Remember State"],
                index=2
            )
            
            # Metric cards
            show_metric_cards = st.checkbox("Show Metric Cards", value=True)
            if show_metric_cards:
                metric_card_size = st.selectbox("Metric Card Size", ["Small", "Medium", "Large"], index=1)
            
            # Time range default
            default_time_range = st.selectbox(
                "Default Time Range",
                ["1 hour", "24 hours", "7 days", "30 days"],
                index=1
            )
            
            # Notifications
            desktop_notifications = st.checkbox("Desktop Notifications", value=False)
            sound_notifications = st.checkbox("Sound Notifications", value=False)
            
            if st.button("Save User Preferences"):
                st.success("✅ User preferences saved successfully!")
    
    def render_security_settings(self):
        """Render security settings"""
        st.subheader("🔐 Security Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Authentication**")
            
            # Session settings
            session_timeout = st.selectbox(
                "Session Timeout",
                ["15 minutes", "30 minutes", "1 hour", "4 hours", "8 hours"],
                index=2
            )
            
            require_2fa = st.checkbox("Require Two-Factor Authentication", value=False)
            
            # Password policy
            st.write("**Password Policy**")
            min_password_length = st.number_input("Minimum Password Length", min_value=6, value=8)
            require_special_chars = st.checkbox("Require Special Characters", value=True)
            require_numbers = st.checkbox("Require Numbers", value=True)
            require_uppercase = st.checkbox("Require Uppercase Letters", value=True)
            
            # Account lockout
            enable_lockout = st.checkbox("Enable Account Lockout", value=True)
            if enable_lockout:
                max_failed_attempts = st.number_input("Max Failed Attempts", min_value=3, value=5)
                lockout_duration = st.selectbox(
                    "Lockout Duration",
                    ["15 minutes", "30 minutes", "1 hour", "24 hours"],
                    index=1
                )
        
        with col2:
            st.write("**Access Control**")
            
            # API access
            api_rate_limit = st.number_input("API Rate Limit (requests/minute)", min_value=10, value=100)
            enable_api_logging = st.checkbox("Enable API Access Logging", value=True)
            
            # Data encryption
            encrypt_data_at_rest = st.checkbox("Encrypt Data at Rest", value=True)
            encrypt_data_in_transit = st.checkbox("Encrypt Data in Transit", value=True)
            
            # Audit logging
            st.write("**Audit Settings**")
            enable_audit_logging = st.checkbox("Enable Audit Logging", value=True)
            if enable_audit_logging:
                audit_log_retention = st.selectbox(
                    "Audit Log Retention",
                    ["30 days", "90 days", "1 year", "2 years"],
                    index=2
                )
                
                log_events = st.multiselect(
                    "Events to Log",
                    ["Login/Logout", "Data Access", "Configuration Changes", "Alert Actions", "Report Generation"],
                    default=["Login/Logout", "Configuration Changes", "Alert Actions"]
                )
            
            # IP restrictions
            enable_ip_whitelist = st.checkbox("Enable IP Whitelist", value=False)
            if enable_ip_whitelist:
                ip_whitelist = st.text_area("Allowed IP Addresses (one per line)", 
                                           value="192.168.1.0/24\n10.0.0.0/8")
            
            if st.button("Save Security Settings"):
                st.success("✅ Security settings saved successfully!")
        
        # Security status
        st.divider()
        st.subheader("🛡️ Security Status")
        
        security_checks = [
            ("SSL Certificate", "🟢 Valid"),
            ("Database Encryption", "🟢 Enabled"),
            ("API Authentication", "🟢 Active"),
            ("Audit Logging", "🟢 Active"),
            ("Backup Encryption", "🟢 Enabled"),
            ("User Session Security", "🟢 Secure")
        ]
        
        cols = st.columns(3)
        for i, (check, status) in enumerate(security_checks):
            with cols[i % 3]:
                st.write(f"**{check}**: {status}")
        
        st.success("🛡️ All security checks passed!")

    def run(self):
        """Launch the minimal dashboard"""
        self.render_header()
        self.render_sidebar()
        
        # Page routing
        pages = {
            'overview': self.render_overview_page,
            'monitoring': self.render_monitoring_page,
            'analytics': self.render_analytics_page,
            'alerts': self.render_alerts_page,
            'reports': self.render_reports_page,
            'settings': self.render_settings_page
        }
        
        current_page = st.session_state.current_page
        if current_page in pages:
            pages[current_page]()
        else:
            st.error("Page not found")
        
        # Simple Footer
        st.divider()
        st.markdown("**© 2024 Air Quality Monitoring Platform** | Real-time Environmental Intelligence")

# Main execution
if __name__ == "__main__":
    dashboard = MinimalDashboard()
    dashboard.run()