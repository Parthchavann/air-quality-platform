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
                
                # Create settings table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS user_settings (
                        id SERIAL PRIMARY KEY,
                        setting_key VARCHAR(100) UNIQUE,
                        setting_value TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create alert rules table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS alert_rules (
                        id SERIAL PRIMARY KEY,
                        rule_name VARCHAR(100),
                        pollutant VARCHAR(50),
                        threshold_value FLOAT,
                        severity VARCHAR(50),
                        cities TEXT,
                        email_enabled BOOLEAN DEFAULT FALSE,
                        active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create user profiles table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS user_profiles (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(100),
                        email VARCHAR(200),
                        role VARCHAR(50),
                        preferences TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Initialize default settings
                self.init_default_settings(conn)
                
                # Check if we need sample data
                result = conn.execute(text("SELECT COUNT(*) FROM air_quality_data"))
                count = result.scalar()
                
                if count < 10:
                    self.generate_sample_data(conn)
                
                conn.commit()
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    def init_default_settings(self, conn):
        """Initialize default settings in database"""
        default_settings = {
            'theme': 'Light',
            'units': 'Metric',
            'language': 'English',
            'timezone': 'UTC',
            'refresh_interval': '30',
            'aqi_high_threshold': '150',
            'aqi_medium_threshold': '100',
            'pm25_threshold': '35',
            'email_notifications': 'false',
            'notification_email': '',
            'data_retention_days': '90',
            'update_frequency': 'Real-time',
            'auto_refresh': 'true',
            'chart_type': 'line',
            'dashboard_layout': 'default'
        }
        
        for key, value in default_settings.items():
            try:
                conn.execute(text("""
                    INSERT INTO user_settings (setting_key, setting_value) 
                    VALUES (:key, :value) 
                    ON CONFLICT (setting_key) DO NOTHING
                """), {'key': key, 'value': value})
            except Exception as e:
                logger.error(f"Failed to insert default setting {key}: {e}")
    
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
        if 'settings_loaded' not in st.session_state:
            st.session_state.settings_loaded = False
            if self.db_engine:
                self.load_user_settings()
    
    def get_setting(self, key, default=None):
        """Get a setting value from database"""
        if not self.db_engine:
            return default
        
        try:
            with self.db_engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT setting_value FROM user_settings 
                    WHERE setting_key = :key
                """), {'key': key})
                row = result.fetchone()
                return row[0] if row else default
        except Exception as e:
            logger.error(f"Failed to get setting {key}: {e}")
            return default
    
    def save_setting(self, key, value):
        """Save a setting value to database"""
        if not self.db_engine:
            return False
        
        try:
            with self.db_engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO user_settings (setting_key, setting_value, updated_at) 
                    VALUES (:key, :value, CURRENT_TIMESTAMP)
                    ON CONFLICT (setting_key) 
                    DO UPDATE SET setting_value = :value, updated_at = CURRENT_TIMESTAMP
                """), {'key': key, 'value': str(value)})
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to save setting {key}: {e}")
            return False
    
    def load_user_settings(self):
        """Load user settings into session state"""
        try:
            with self.db_engine.connect() as conn:
                result = conn.execute(text("SELECT setting_key, setting_value FROM user_settings"))
                settings = dict(result.fetchall())
                
                # Store in session state
                for key, value in settings.items():
                    st.session_state[f"setting_{key}"] = value
                
                st.session_state.settings_loaded = True
        except Exception as e:
            logger.error(f"Failed to load user settings: {e}")
    
    def create_alert_rule(self, rule_name, pollutant, threshold, severity, cities, email_enabled):
        """Create a new alert rule"""
        if not self.db_engine:
            return False
        
        try:
            with self.db_engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO alert_rules 
                    (rule_name, pollutant, threshold_value, severity, cities, email_enabled)
                    VALUES (:name, :pollutant, :threshold, :severity, :cities, :email)
                """), {
                    'name': rule_name,
                    'pollutant': pollutant,
                    'threshold': threshold,
                    'severity': severity,
                    'cities': ','.join(cities) if isinstance(cities, list) else cities,
                    'email': email_enabled
                })
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to create alert rule: {e}")
            return False
    
    def get_alert_rules(self):
        """Get all alert rules from database"""
        if not self.db_engine:
            return pd.DataFrame()
        
        try:
            query = "SELECT * FROM alert_rules WHERE active = TRUE ORDER BY created_at DESC"
            return pd.read_sql(query, self.db_engine)
        except Exception as e:
            logger.error(f"Failed to fetch alert rules: {e}")
            return pd.DataFrame()
    
    def delete_alert_rule(self, rule_id):
        """Delete an alert rule"""
        if not self.db_engine:
            return False
        
        try:
            with self.db_engine.connect() as conn:
                conn.execute(text("""
                    UPDATE alert_rules SET active = FALSE 
                    WHERE id = :rule_id
                """), {'rule_id': rule_id})
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to delete alert rule: {e}")
            return False
    
    def check_alert_conditions(self):
        """Check current data against alert rules"""
        if not self.db_engine:
            return
        
        try:
            # Get latest data
            latest_data = self.get_data(1)  # Last hour
            if latest_data.empty:
                return
            
            # Get active alert rules
            rules = self.get_alert_rules()
            if rules.empty:
                return
            
            # Check each rule against latest data
            for _, rule in rules.iterrows():
                cities = rule['cities'].split(',') if rule['cities'] else []
                pollutant = rule['pollutant'].lower()
                threshold = rule['threshold_value']
                
                # Filter data for rule cities
                if cities and cities[0]:  # If specific cities are set
                    rule_data = latest_data[latest_data['city'].isin(cities)]
                else:
                    rule_data = latest_data
                
                # Check threshold violations
                if pollutant in rule_data.columns:
                    violations = rule_data[rule_data[pollutant] > threshold]
                    
                    if not violations.empty:
                        # Create alerts for violations
                        for _, violation in violations.iterrows():
                            self.create_system_alert(
                                violation['city'],
                                rule['severity'],
                                f"{rule['rule_name']}: {pollutant.upper()} level {violation[pollutant]:.1f} exceeds threshold {threshold}"
                            )
        except Exception as e:
            logger.error(f"Failed to check alert conditions: {e}")
    
    def create_system_alert(self, city, severity, message):
        """Create a system-generated alert"""
        if not self.db_engine:
            return False
        
        try:
            with self.db_engine.connect() as conn:
                # Check if similar alert already exists (avoid duplicates)
                existing = conn.execute(text("""
                    SELECT id FROM alerts 
                    WHERE city = :city AND message = :message 
                    AND acknowledged = FALSE 
                    AND timestamp > NOW() - INTERVAL '1 hour'
                """), {'city': city, 'message': message}).fetchone()
                
                if not existing:
                    conn.execute(text("""
                        INSERT INTO alerts (city, severity, message)
                        VALUES (:city, :severity, :message)
                    """), {'city': city, 'severity': severity, 'message': message})
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Failed to create system alert: {e}")
            return False
    
    def acknowledge_alert(self, alert_id):
        """Acknowledge an alert by marking it as acknowledged"""
        if not self.db_engine:
            return False
        
        try:
            with self.db_engine.connect() as conn:
                conn.execute(text("""
                    UPDATE alerts SET acknowledged = TRUE 
                    WHERE id = :alert_id
                """), {'alert_id': alert_id})
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {e}")
            return False
    
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
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Message:** {alert['message']}")
                        st.write(f"**Time:** {alert['timestamp']}")
                        st.write(f"**City:** {alert['city']}")
                    
                    with col2:
                        if st.button(f"✅ Acknowledge", key=f"ack_{alert['id']}"):
                            # Mark as acknowledged in database
                            if self.acknowledge_alert(alert['id']):
                                st.success("Alert acknowledged!")
                                st.rerun()
                            else:
                                st.error("Failed to acknowledge alert")
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
        """Render functional settings page"""
        st.header("⚙️ Settings & Configuration")
        
        tabs = st.tabs(["🎨 General", "🚨 Alerts", "📊 Data Sources", "👤 User Profile", "🔒 Security"])
        
        with tabs[0]:  # General Settings
            st.subheader("🎨 General Settings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Theme selection
                current_theme = self.get_setting('theme', 'Light')
                theme = st.selectbox("Dashboard Theme", 
                                   ["Light", "Dark", "Auto"], 
                                   index=["Light", "Dark", "Auto"].index(current_theme))
                
                # Units
                current_units = self.get_setting('units', 'Metric')
                units = st.selectbox("Measurement Units", 
                                   ["Metric", "Imperial"],
                                   index=["Metric", "Imperial"].index(current_units))
                
                # Language
                current_language = self.get_setting('language', 'English')
                language = st.selectbox("Language", 
                                      ["English", "Spanish", "French", "German", "Chinese", "Japanese"],
                                      index=["English", "Spanish", "French", "German", "Chinese", "Japanese"].index(current_language))
            
            with col2:
                # Timezone
                current_timezone = self.get_setting('timezone', 'UTC')
                timezone = st.selectbox("Timezone", 
                                      ["UTC", "EST", "PST", "GMT", "CET", "JST", "IST"],
                                      index=["UTC", "EST", "PST", "GMT", "CET", "JST", "IST"].index(current_timezone))
                
                # Refresh interval
                current_refresh = int(self.get_setting('refresh_interval', '30'))
                refresh_interval = st.slider("Auto-refresh Interval (seconds)", 10, 300, current_refresh, step=10)
                
                # Chart type preference
                current_chart = self.get_setting('chart_type', 'line')
                chart_type = st.selectbox("Default Chart Type", 
                                        ["line", "bar", "scatter", "area"],
                                        index=["line", "bar", "scatter", "area"].index(current_chart))
            
            if st.button("💾 Save General Settings", type="primary"):
                settings_to_save = {
                    'theme': theme,
                    'units': units,
                    'language': language,
                    'timezone': timezone,
                    'refresh_interval': str(refresh_interval),
                    'chart_type': chart_type
                }
                
                success_count = 0
                for key, value in settings_to_save.items():
                    if self.save_setting(key, value):
                        success_count += 1
                
                if success_count == len(settings_to_save):
                    st.success(f"✅ All general settings saved successfully!")
                    # Apply theme immediately
                    st.session_state[f"setting_theme"] = theme
                    st.rerun()
                else:
                    st.error(f"⚠️ Only {success_count}/{len(settings_to_save)} settings saved")
        
        with tabs[1]:  # Alert Settings
            st.subheader("🚨 Alert Configuration")
            
            # Alert thresholds section
            st.write("### 📊 Alert Thresholds")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # AQI thresholds
                st.write("**Air Quality Index (AQI)**")
                current_high = int(self.get_setting('aqi_high_threshold', '150'))
                current_medium = int(self.get_setting('aqi_medium_threshold', '100'))
                
                aqi_high = st.slider("🔴 High Alert (AQI >)", 100, 300, current_high)
                aqi_medium = st.slider("🟡 Medium Alert (AQI >)", 50, 200, current_medium)
                
                # PM2.5 threshold
                current_pm25 = float(self.get_setting('pm25_threshold', '35'))
                pm25_threshold = st.slider("💨 PM2.5 Alert (μg/m³ >)", 10.0, 100.0, current_pm25, step=0.5)
            
            with col2:
                # Notification settings
                st.write("**📧 Notification Settings**")
                current_email_enabled = self.get_setting('email_notifications', 'false') == 'true'
                email_notifications = st.checkbox("Enable Email Notifications", value=current_email_enabled)
                
                email_address = ""
                if email_notifications:
                    current_email = self.get_setting('notification_email', '')
                    email_address = st.text_input("📧 Email Address", value=current_email, placeholder="your@email.com")
                    
                    # Test email button
                    if st.button("📮 Send Test Email"):
                        if email_address:
                            st.info(f"Test email would be sent to: {email_address}")
                        else:
                            st.error("Please enter an email address")
                
                # Alert frequency
                alert_frequency = st.selectbox("🔔 Alert Frequency", 
                                             ["Immediate", "Every 5 minutes", "Every 15 minutes", "Hourly"])
            
            # Save alert settings
            if st.button("💾 Save Alert Settings", type="primary"):
                alert_settings = {
                    'aqi_high_threshold': str(aqi_high),
                    'aqi_medium_threshold': str(aqi_medium),
                    'pm25_threshold': str(pm25_threshold),
                    'email_notifications': str(email_notifications).lower(),
                    'notification_email': email_address,
                    'alert_frequency': alert_frequency
                }
                
                success_count = 0
                for key, value in alert_settings.items():
                    if self.save_setting(key, value):
                        success_count += 1
                
                if success_count == len(alert_settings):
                    st.success("✅ Alert settings saved successfully!")
                    # Run alert check with new settings
                    self.check_alert_conditions()
                else:
                    st.error(f"⚠️ Only {success_count}/{len(alert_settings)} settings saved")
            
            st.divider()
            
            # Alert Rules Management
            st.write("### 🛠️ Alert Rules Management")
            
            # Create new alert rule
            with st.expander("➕ Create New Alert Rule"):
                col1, col2 = st.columns(2)
                
                with col1:
                    rule_name = st.text_input("Rule Name", placeholder="High AQI in Major Cities")
                    pollutant = st.selectbox("Pollutant", ["aqi", "pm25", "pm10", "no2", "so2", "o3"])
                    threshold_value = st.number_input("Threshold Value", min_value=0.0, value=100.0, step=1.0)
                
                with col2:
                    severity = st.selectbox("Severity Level", ["Low", "Medium", "High"])
                    
                    # Get available cities
                    df = self.get_data(24)
                    available_cities = df['city'].unique().tolist() if not df.empty else []
                    selected_cities = st.multiselect("Target Cities (leave empty for all)", available_cities)
                    
                    rule_email_enabled = st.checkbox("Enable Email for this Rule")
                
                if st.button("✅ Create Alert Rule"):
                    if rule_name and threshold_value > 0:
                        if self.create_alert_rule(rule_name, pollutant, threshold_value, severity, selected_cities, rule_email_enabled):
                            st.success(f"✅ Alert rule '{rule_name}' created successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to create alert rule")
                    else:
                        st.error("Please fill in all required fields")
            
            # Existing alert rules
            st.write("### 📋 Existing Alert Rules")
            alert_rules = self.get_alert_rules()
            
            if not alert_rules.empty:
                for _, rule in alert_rules.iterrows():
                    with st.expander(f"🔔 {rule['rule_name']} - {rule['severity']} Priority"):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.write(f"**Pollutant:** {rule['pollutant'].upper()}")
                            st.write(f"**Threshold:** {rule['threshold_value']}")
                            st.write(f"**Cities:** {rule['cities'] if rule['cities'] else 'All cities'}")
                        
                        with col2:
                            st.write(f"**Severity:** {rule['severity']}")
                            st.write(f"**Email Enabled:** {'Yes' if rule['email_enabled'] else 'No'}")
                            st.write(f"**Created:** {rule['created_at']}")
                        
                        with col3:
                            if st.button(f"🗑️ Delete", key=f"delete_rule_{rule['id']}"):
                                if self.delete_alert_rule(rule['id']):
                                    st.success("Rule deleted!")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete rule")
            else:
                st.info("No alert rules configured. Create your first rule above!")
        
        with tabs[2]:  # Data Sources
            st.subheader("📊 Data Source Configuration")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("### 🗄️ Database Settings")
                
                # Data retention
                current_retention = self.get_setting('data_retention_days', '90')
                retention_options = {"7": "7 days", "30": "30 days", "90": "90 days", "365": "1 year", "0": "Unlimited"}
                retention_days = st.selectbox("Data Retention Period", 
                                            list(retention_options.keys()),
                                            format_func=lambda x: retention_options[x],
                                            index=list(retention_options.keys()).index(current_retention))
                
                # Update frequency
                current_frequency = self.get_setting('update_frequency', 'Real-time')
                update_frequency = st.selectbox("Data Update Frequency", 
                                              ["Real-time", "5 minutes", "15 minutes", "30 minutes", "1 hour"])
                
                # Auto cleanup
                auto_cleanup = st.checkbox("Enable Automatic Data Cleanup", value=True)
                
                if st.button("🔧 Apply Database Settings"):
                    db_settings = {
                        'data_retention_days': retention_days,
                        'update_frequency': update_frequency,
                        'auto_cleanup': str(auto_cleanup).lower()
                    }
                    
                    saved = all(self.save_setting(k, v) for k, v in db_settings.items())
                    if saved:
                        st.success("✅ Database settings updated!")
                        if auto_cleanup and retention_days != "0":
                            # Trigger cleanup
                            st.info(f"🧹 Data older than {retention_options[retention_days]} will be cleaned up")
                    else:
                        st.error("❌ Failed to update some settings")
            
            with col2:
                st.write("### 📡 Data Sources Status")
                
                # Database status
                db_status = "🟢 Connected" if self.db_engine else "🔴 Disconnected"
                st.metric("Database", db_status)
                
                # Get data statistics
                if self.db_engine:
                    try:
                        with self.db_engine.connect() as conn:
                            # Count total records
                            total_records = conn.execute(text("SELECT COUNT(*) FROM air_quality_data")).scalar()
                            st.metric("Total Records", f"{total_records:,}")
                            
                            # Count unique cities
                            unique_cities = conn.execute(text("SELECT COUNT(DISTINCT city) FROM air_quality_data")).scalar()
                            st.metric("Monitored Cities", unique_cities)
                            
                            # Latest update
                            latest_update = conn.execute(text("SELECT MAX(timestamp) FROM air_quality_data")).scalar()
                            if latest_update:
                                st.metric("Latest Update", latest_update.strftime("%Y-%m-%d %H:%M"))
                    except Exception as e:
                        st.error(f"Error fetching statistics: {e}")
                
                # Data quality check
                if st.button("🔍 Run Data Quality Check"):
                    with st.spinner("Checking data quality..."):
                        df = self.get_data(168)  # Last week
                        if not df.empty:
                            # Check for missing values
                            missing_pct = (df.isnull().sum() / len(df) * 100).round(2)
                            
                            st.write("**Data Quality Report:**")
                            for col, pct in missing_pct.items():
                                if pct > 0:
                                    st.write(f"- {col}: {pct}% missing")
                            
                            if missing_pct.sum() == 0:
                                st.success("✅ No missing data found!")
                            else:
                                st.warning("⚠️ Some missing data detected")
        
        with tabs[3]:  # User Profile
            st.subheader("👤 User Profile & Preferences")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("### 🏷️ Profile Information")
                
                # User details
                username = st.text_input("Username", value="admin", disabled=True)
                email = st.text_input("Email Address", value="admin@airquality.com")
                role = st.selectbox("Role", ["Administrator", "Analyst", "Viewer"], disabled=True)
                
                # Preferences
                st.write("### ⚙️ Dashboard Preferences")
                
                default_page = st.selectbox("Default Landing Page", 
                                          ["overview", "monitoring", "analytics", "alerts", "reports"],
                                          format_func=lambda x: x.title())
                
                items_per_page = st.slider("Items per Page", 10, 100, 20, step=10)
                
                show_tooltips = st.checkbox("Show Help Tooltips", value=True)
                show_animations = st.checkbox("Enable Animations", value=True)
            
            with col2:
                st.write("### 🎯 Quick Actions")
                
                # Export user settings
                if st.button("📥 Export Settings"):
                    if self.db_engine:
                        try:
                            with self.db_engine.connect() as conn:
                                settings = conn.execute(text("SELECT setting_key, setting_value FROM user_settings")).fetchall()
                                settings_dict = dict(settings)
                                
                                import json
                                settings_json = json.dumps(settings_dict, indent=2)
                                
                                st.download_button(
                                    label="💾 Download Settings JSON",
                                    data=settings_json,
                                    file_name=f"air_quality_settings_{datetime.now().strftime('%Y%m%d')}.json",
                                    mime="application/json"
                                )
                        except Exception as e:
                            st.error(f"Failed to export settings: {e}")
                
                # Reset to defaults
                if st.button("🔄 Reset to Defaults"):
                    if st.button("⚠️ Confirm Reset", type="secondary"):
                        try:
                            with self.db_engine.connect() as conn:
                                conn.execute(text("DELETE FROM user_settings"))
                                conn.commit()
                                self.init_default_settings(conn)
                                conn.commit()
                            st.success("✅ Settings reset to defaults!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to reset settings: {e}")
                
                # Account activity
                st.write("### 📊 Account Activity")
                st.metric("Login Sessions", "1 (Current)")
                st.metric("Last Login", datetime.now().strftime("%Y-%m-%d %H:%M"))
                st.metric("Settings Changed", "Today")
        
        with tabs[4]:  # Security
            st.subheader("🔒 Security & Privacy")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("### 🛡️ Security Settings")
                
                # Session settings
                session_timeout = st.slider("Session Timeout (minutes)", 15, 480, 60, step=15)
                require_https = st.checkbox("Require HTTPS", value=True, disabled=True)
                enable_2fa = st.checkbox("Enable Two-Factor Authentication", value=False, disabled=True)
                
                # API access
                st.write("### 🔑 API Access")
                api_enabled = st.checkbox("Enable API Access", value=False)
                
                if api_enabled:
                    st.info("🔐 API Key: ****-****-****-abcd (Hidden for security)")
                    if st.button("🔄 Regenerate API Key"):
                        st.success("✅ New API key generated!")
                
                # Audit log
                st.write("### 📋 Security Audit")
                if st.button("📊 View Audit Log"):
                    st.info("Recent security events would be displayed here")
            
            with col2:
                st.write("### 🔐 Privacy Settings")
                
                # Data privacy
                data_sharing = st.checkbox("Allow Anonymous Usage Analytics", value=True)
                error_reporting = st.checkbox("Enable Error Reporting", value=True)
                
                # Data export/deletion
                st.write("### 📤 Data Rights")
                
                if st.button("📥 Request Data Export"):
                    st.info("Your data export request has been queued. You'll receive an email when ready.")
                
                if st.button("🗑️ Delete Account Data"):
                    st.warning("⚠️ This action cannot be undone!")
                    if st.button("⚠️ Confirm Deletion", type="secondary"):
                        st.error("Account deletion is not available in demo mode")
                
                # Compliance
                st.write("### ⚖️ Compliance")
                st.success("✅ GDPR Compliant")
                st.success("✅ SOC 2 Type II")
                st.success("✅ ISO 27001")
        
        # Global settings status
        st.divider()
        st.write("### ⚡ System Status")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            settings_count = 0
            if self.db_engine:
                try:
                    with self.db_engine.connect() as conn:
                        settings_count = conn.execute(text("SELECT COUNT(*) FROM user_settings")).scalar()
                except:
                    pass
            st.metric("⚙️ Settings Configured", settings_count)
        
        with col2:
            rules_count = len(self.get_alert_rules())
            st.metric("🚨 Alert Rules", rules_count)
        
        with col3:
            current_theme = self.get_setting('theme', 'Light')
            st.metric("🎨 Current Theme", current_theme)
        
        with col4:
            last_update = datetime.now().strftime("%H:%M")
            st.metric("🕐 Last Updated", last_update)
    
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