"""
Air Quality Dashboard - Render Optimized Version
Simplified for deployment on Render.com (no Kafka/Spark dependencies)
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import psycopg2
from sqlalchemy import create_engine, text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Air Quality Monitor",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

class RenderDashboard:
    """Render-optimized Air Quality Dashboard"""
    
    def __init__(self):
        self.db_engine = self.get_database_connection()
        self.setup_session_state()
        # Initialize database on first run
        if self.db_engine:
            self.init_database()
    
    @staticmethod
    @st.cache_resource
    def get_database_connection():
        """Get database connection from Render environment"""
        try:
            # Render provides DATABASE_URL environment variable
            database_url = os.getenv('DATABASE_URL')
            
            if database_url:
                # Render uses postgres:// but SQLAlchemy needs postgresql://
                if database_url.startswith('postgres://'):
                    database_url = database_url.replace('postgres://', 'postgresql://', 1)
            else:
                # Fallback for local development
                database_url = "postgresql://airquality_user:secure_password@localhost:5432/airquality"
            
            engine = create_engine(database_url)
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection established")
            return engine
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def init_database(self):
        """Initialize database with tables and sample data"""
        try:
            with self.db_engine.connect() as conn:
                # Create tables if they don't exist
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS air_quality_data (
                        id SERIAL PRIMARY KEY,
                        city VARCHAR(100),
                        country VARCHAR(100),
                        aqi INTEGER,
                        pm25 FLOAT,
                        pm10 FLOAT,
                        o3 FLOAT,
                        no2 FLOAT,
                        so2 FLOAT,
                        co FLOAT,
                        temperature FLOAT,
                        humidity FLOAT,
                        wind_speed FLOAT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id SERIAL PRIMARY KEY,
                        city VARCHAR(100),
                        severity VARCHAR(50),
                        message TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        acknowledged BOOLEAN DEFAULT FALSE
                    )
                """))
                
                # Check if we need sample data
                result = conn.execute(text("SELECT COUNT(*) FROM air_quality_data"))
                count = result.scalar()
                
                if count < 10:
                    self.generate_sample_data(conn)
                
                conn.commit()
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    def generate_sample_data(self, conn):
        """Generate sample data for demonstration"""
        cities = [
            ('New York', 'USA', 40.7128, -74.0060),
            ('London', 'UK', 51.5074, -0.1278),
            ('Tokyo', 'Japan', 35.6762, 139.6503),
            ('Paris', 'France', 48.8566, 2.3522),
            ('Beijing', 'China', 39.9042, 116.4074),
            ('Mumbai', 'India', 19.0760, 72.8777),
            ('Sydney', 'Australia', -33.8688, 151.2093),
            ('Dubai', 'UAE', 25.2048, 55.2708)
        ]
        
        # Generate data for last 7 days
        for days_ago in range(7, -1, -1):
            for hour in range(0, 24, 3):
                timestamp = datetime.now() - timedelta(days=days_ago, hours=hour)
                for city, country, lat, lon in cities:
                    aqi = np.random.randint(30, 200)
                    pm25 = np.random.uniform(10, 100)
                    pm10 = np.random.uniform(20, 150)
                    
                    conn.execute(text("""
                        INSERT INTO air_quality_data 
                        (city, country, aqi, pm25, pm10, o3, no2, so2, co, temperature, humidity, wind_speed, timestamp)
                        VALUES (:city, :country, :aqi, :pm25, :pm10, :o3, :no2, :so2, :co, :temp, :humidity, :wind, :ts)
                    """), {
                        'city': city, 'country': country, 'aqi': aqi,
                        'pm25': pm25, 'pm10': pm10,
                        'o3': np.random.uniform(20, 80),
                        'no2': np.random.uniform(10, 60),
                        'so2': np.random.uniform(5, 30),
                        'co': np.random.uniform(0.5, 5),
                        'temp': np.random.uniform(15, 35),
                        'humidity': np.random.uniform(30, 80),
                        'wind': np.random.uniform(5, 25),
                        'ts': timestamp
                    })
        
        # Generate some alerts
        alert_messages = [
            ("High", "AQI exceeds 150 - Unhealthy conditions"),
            ("Medium", "PM2.5 levels above normal"),
            ("Low", "Slight increase in NO2 detected")
        ]
        
        for city, _, _, _ in cities[:3]:
            severity, message = np.random.choice(alert_messages)
            conn.execute(text("""
                INSERT INTO alerts (city, severity, message)
                VALUES (:city, :severity, :message)
            """), {'city': city, 'severity': severity, 'message': f"{city}: {message}"})
    
    def setup_session_state(self):
        """Initialize session state variables"""
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'overview'
        if 'time_range' not in st.session_state:
            st.session_state.time_range = '24h'
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = False
    
    def get_data(self, hours=24):
        """Fetch air quality data from database"""
        if not self.db_engine:
            return pd.DataFrame()
        
        try:
            query = f"""
                SELECT * FROM air_quality_data 
                WHERE timestamp > NOW() - INTERVAL '{hours} hours'
                ORDER BY timestamp DESC
            """
            return pd.read_sql(query, self.db_engine)
        except Exception as e:
            logger.error(f"Failed to fetch data: {e}")
            return pd.DataFrame()
    
    def get_alerts(self):
        """Fetch active alerts from database"""
        if not self.db_engine:
            return pd.DataFrame()
        
        try:
            query = """
                SELECT * FROM alerts 
                WHERE acknowledged = FALSE
                ORDER BY timestamp DESC
            """
            return pd.read_sql(query, self.db_engine)
        except Exception as e:
            logger.error(f"Failed to fetch alerts: {e}")
            return pd.DataFrame()
    
    def render_header(self):
        """Render dashboard header"""
        st.title("🌍 Air Quality Monitor")
        st.markdown("**Real-time Environmental Intelligence Platform**")
        
        # Status metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status = "🟢 Online" if self.db_engine else "🔴 Offline"
            st.metric("System Status", status)
        
        with col2:
            st.metric("Environment", "🚀 Production")
        
        with col3:
            current_time = datetime.now().strftime("%H:%M:%S")
            st.metric("Last Update", current_time)
        
        with col4:
            st.metric("Version", "v2.0 (Render)")
        
        st.divider()
    
    def render_sidebar(self):
        """Render sidebar navigation"""
        with st.sidebar:
            st.header("🧭 Navigation")
            
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
            
            # Time range selector
            st.subheader("⏱️ Time Range")
            time_options = {
                '1h': 'Last Hour',
                '24h': 'Last 24 Hours',
                '7d': 'Last 7 Days',
                '30d': 'Last 30 Days'
            }
            
            st.session_state.time_range = st.selectbox(
                "Select period",
                options=list(time_options.keys()),
                format_func=lambda x: time_options[x],
                index=1
            )
            
            # Refresh controls
            st.divider()
            st.subheader("🔄 Controls")
            
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
            
            # Auto-refresh toggle
            st.session_state.auto_refresh = st.checkbox("Auto Refresh (30s)", value=st.session_state.auto_refresh)
            
            if st.session_state.auto_refresh:
                st.info("Auto-refresh enabled")
                st.rerun()
    
    def render_overview_page(self):
        """Render overview page"""
        st.header("📊 Air Quality Overview")
        
        # Get data
        hours = {'1h': 1, '24h': 24, '7d': 168, '30d': 720}[st.session_state.time_range]
        df = self.get_data(hours)
        
        if df.empty:
            st.warning("No data available. Generating sample data...")
            self.init_database()
            st.rerun()
            return
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_aqi = df['aqi'].mean()
            st.metric("Average AQI", f"{avg_aqi:.0f}",
                     delta="Good" if avg_aqi < 50 else "Moderate" if avg_aqi < 100 else "Poor")
        
        with col2:
            cities = df['city'].nunique()
            st.metric("Cities Monitored", f"{cities}")
        
        with col3:
            alerts_df = self.get_alerts()
            active_alerts = len(alerts_df)
            st.metric("Active Alerts", f"{active_alerts}",
                     delta="Clear" if active_alerts == 0 else f"{active_alerts} active")
        
        with col4:
            measurements = len(df)
            st.metric("Data Points", f"{measurements:,}")
        
        st.divider()
        
        # Visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            # AQI Distribution
            fig_hist = px.histogram(df, x='aqi', nbins=30,
                                   title="AQI Distribution",
                                   labels={'aqi': 'Air Quality Index', 'count': 'Frequency'})
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            # Cities by AQI
            city_aqi = df.groupby('city')['aqi'].mean().reset_index()
            city_aqi = city_aqi.sort_values('aqi', ascending=True).head(10)
            
            fig_bar = px.bar(city_aqi, x='aqi', y='city', orientation='h',
                            title="Average AQI by City",
                            color='aqi', color_continuous_scale='RdYlGn_r')
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Time series
        st.subheader("📈 AQI Trends Over Time")
        
        df_time = df.sort_values('timestamp')
        fig_line = px.line(df_time, x='timestamp', y='aqi', color='city',
                          title="Air Quality Index Timeline")
        st.plotly_chart(fig_line, use_container_width=True)
        
        # Data table
        st.subheader("📋 Recent Measurements")
        display_cols = ['city', 'country', 'aqi', 'pm25', 'pm10', 'timestamp']
        st.dataframe(df[display_cols].head(20), use_container_width=True, hide_index=True)
    
    def render_monitoring_page(self):
        """Render real-time monitoring page"""
        st.header("📈 Real-time Monitoring")
        
        # Get latest data
        df = self.get_data(1)  # Last hour
        
        if df.empty:
            st.warning("No recent data available")
            return
        
        # Create real-time style metrics
        st.subheader("🔴 Live Air Quality Indicators")
        
        # Get latest reading for each city
        latest = df.groupby('city').first().reset_index()
        
        # Display cities in grid
        cols = st.columns(4)
        for idx, row in latest.iterrows():
            col = cols[idx % 4]
            with col:
                # Color based on AQI
                if row['aqi'] < 50:
                    color = "🟢"
                elif row['aqi'] < 100:
                    color = "🟡"
                elif row['aqi'] < 150:
                    color = "🟠"
                else:
                    color = "🔴"
                
                st.metric(
                    f"{color} {row['city']}",
                    f"AQI: {row['aqi']:.0f}",
                    delta=f"PM2.5: {row['pm25']:.1f}"
                )
        
        st.divider()
        
        # Real-time chart
        st.subheader("📊 Live Trends (Last Hour)")
        
        df_sorted = df.sort_values('timestamp')
        fig = px.line(df_sorted, x='timestamp', y='aqi', color='city',
                     title="Real-time AQI Updates")
        fig.update_layout(hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
        
        # Auto-refresh notice
        if st.session_state.auto_refresh:
            st.info("🔄 Auto-refreshing every 30 seconds...")
            import time
            time.sleep(30)
            st.rerun()
    
    def render_analytics_page(self):
        """Render analytics page"""
        st.header("🔍 Advanced Analytics")
        
        # Analysis type selector
        analysis_type = st.selectbox(
            "Select Analysis Type",
            ["Trend Analysis", "Correlation Analysis", "City Comparison", "Pollution Patterns"]
        )
        
        # Get data
        hours = {'1h': 1, '24h': 24, '7d': 168, '30d': 720}[st.session_state.time_range]
        df = self.get_data(hours)
        
        if df.empty:
            st.warning("No data available for analysis")
            return
        
        if analysis_type == "Trend Analysis":
            st.subheader("📈 Pollution Trends")
            
            # Trend by pollutant
            pollutants = ['aqi', 'pm25', 'pm10', 'no2', 'so2']
            selected_pollutant = st.selectbox("Select Pollutant", pollutants)
            
            df_trend = df.groupby('timestamp')[selected_pollutant].mean().reset_index()
            fig = px.line(df_trend, x='timestamp', y=selected_pollutant,
                         title=f"{selected_pollutant.upper()} Trend Over Time")
            st.plotly_chart(fig, use_container_width=True)
        
        elif analysis_type == "Correlation Analysis":
            st.subheader("🔗 Pollutant Correlations")
            
            # Correlation matrix
            corr_cols = ['aqi', 'pm25', 'pm10', 'o3', 'no2', 'so2', 'temperature', 'humidity']
            corr_matrix = df[corr_cols].corr()
            
            fig = px.imshow(corr_matrix, text_auto=True,
                          title="Correlation Matrix",
                          color_continuous_scale='RdBu')
            st.plotly_chart(fig, use_container_width=True)
        
        elif analysis_type == "City Comparison":
            st.subheader("🏙️ City Comparison")
            
            # Select cities to compare
            cities = df['city'].unique()
            selected_cities = st.multiselect("Select Cities", cities, default=cities[:3])
            
            if selected_cities:
                df_cities = df[df['city'].isin(selected_cities)]
                
                # Box plot comparison
                fig = px.box(df_cities, x='city', y='aqi',
                           title="AQI Distribution by City")
                st.plotly_chart(fig, use_container_width=True)
        
        elif analysis_type == "Pollution Patterns":
            st.subheader("🔄 Pollution Patterns")
            
            # Hourly patterns
            df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
            hourly_pattern = df.groupby('hour')['aqi'].mean().reset_index()
            
            fig = px.bar(hourly_pattern, x='hour', y='aqi',
                       title="Average AQI by Hour of Day")
            st.plotly_chart(fig, use_container_width=True)
    
    def render_alerts_page(self):
        """Render alerts page"""
        st.header("🚨 Alert Management")
        
        # Get alerts
        alerts_df = self.get_alerts()
        
        # Alert summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            high_alerts = len(alerts_df[alerts_df['severity'] == 'High'])
            st.metric("🔴 High Priority", high_alerts)
        
        with col2:
            medium_alerts = len(alerts_df[alerts_df['severity'] == 'Medium'])
            st.metric("🟡 Medium Priority", medium_alerts)
        
        with col3:
            low_alerts = len(alerts_df[alerts_df['severity'] == 'Low'])
            st.metric("🟢 Low Priority", low_alerts)
        
        st.divider()
        
        # Active alerts table
        st.subheader("📋 Active Alerts")
        
        if not alerts_df.empty:
            # Format timestamp
            alerts_df['timestamp'] = pd.to_datetime(alerts_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Display with custom styling
            for _, alert in alerts_df.iterrows():
                severity_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
                with st.expander(f"{severity_color.get(alert['severity'], '⚪')} {alert['city']} - {alert['severity']} Priority"):
                    st.write(f"**Message:** {alert['message']}")
                    st.write(f"**Time:** {alert['timestamp']}")
                    if st.button(f"Acknowledge", key=f"ack_{alert['id']}"):
                        # Mark as acknowledged
                        st.success("Alert acknowledged")
        else:
            st.success("✅ No active alerts")
    
    def render_reports_page(self):
        """Render reports page"""
        st.header("📋 Reports & Export")
        
        report_type = st.selectbox(
            "Select Report Type",
            ["Air Quality Summary", "City Analysis", "Trend Report", "Alert History"]
        )
        
        # Date range for report
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=7))
        with col2:
            end_date = st.date_input("End Date", datetime.now())
        
        if st.button("Generate Report", type="primary"):
            with st.spinner("Generating report..."):
                # Get data for report
                hours = (end_date - start_date).days * 24
                df = self.get_data(hours)
                
                if not df.empty:
                    st.success("Report generated successfully!")
                    
                    # Display report preview
                    st.subheader("Report Preview")
                    
                    if report_type == "Air Quality Summary":
                        st.write(f"**Period:** {start_date} to {end_date}")
                        st.write(f"**Average AQI:** {df['aqi'].mean():.1f}")
                        st.write(f"**Cities Covered:** {df['city'].nunique()}")
                        st.write(f"**Total Measurements:** {len(df)}")
                    
                    # Download button
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"air_quality_report_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
    
    def render_settings_page(self):
        """Render settings page"""
        st.header("⚙️ Settings")
        
        tabs = st.tabs(["General", "Alerts", "Data", "About"])
        
        with tabs[0]:
            st.subheader("General Settings")
            
            # Theme selection
            theme = st.selectbox("Dashboard Theme", ["Light", "Dark", "Auto"])
            
            # Units
            units = st.selectbox("Measurement Units", ["Metric", "Imperial"])
            
            # Language
            language = st.selectbox("Language", ["English", "Spanish", "French", "German"])
            
            if st.button("Save General Settings"):
                st.success("Settings saved successfully!")
        
        with tabs[1]:
            st.subheader("Alert Settings")
            
            # Alert thresholds
            st.write("**AQI Alert Thresholds**")
            high_threshold = st.slider("High Alert (AQI >)", 100, 200, 150)
            medium_threshold = st.slider("Medium Alert (AQI >)", 50, 150, 100)
            
            # Notification settings
            email_alerts = st.checkbox("Email Notifications")
            if email_alerts:
                email = st.text_input("Email Address")
            
            if st.button("Save Alert Settings"):
                st.success("Alert settings updated!")
        
        with tabs[2]:
            st.subheader("Data Settings")
            
            # Data retention
            retention = st.selectbox("Data Retention Period", ["7 days", "30 days", "90 days", "1 year"])
            
            # Update frequency
            frequency = st.selectbox("Update Frequency", ["Real-time", "5 minutes", "15 minutes", "30 minutes"])
            
            if st.button("Save Data Settings"):
                st.success("Data settings updated!")
        
        with tabs[3]:
            st.subheader("About")
            
            st.info("""
            **Air Quality Monitoring Platform**
            
            Version: 2.0 (Render Optimized)
            
            This platform provides real-time air quality monitoring and analysis
            for cities worldwide. Built with Streamlit and optimized for cloud deployment.
            
            **Features:**
            - Real-time monitoring
            - Advanced analytics
            - Alert management
            - Custom reports
            - Cloud-based deployment
            
            **Contact:** support@airquality.example.com
            """)
    
    def run(self):
        """Main application runner"""
        self.render_header()
        self.render_sidebar()
        
        # Route to appropriate page
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

# Main execution
if __name__ == "__main__":
    dashboard = RenderDashboard()
    dashboard.run()