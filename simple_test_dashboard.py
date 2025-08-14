import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="AtmosAnalytics Platform",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'overview'
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False

# Create sample data
@st.cache_data
def generate_sample_data():
    np.random.seed(42)
    dates = pd.date_range(start=datetime.now() - timedelta(days=7), end=datetime.now(), freq='H')
    cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']
    
    data = []
    for date in dates:
        for city in cities:
            aqi = np.random.randint(30, 150)
            pm25 = np.random.uniform(10, 75)
            pm10 = np.random.uniform(20, 100)
            data.append({
                'timestamp': date,
                'city': city,
                'aqi': aqi,
                'pm2.5': pm25,
                'pm10': pm10,
                'temperature': np.random.uniform(15, 35),
                'humidity': np.random.uniform(30, 80)
            })
    
    return pd.DataFrame(data)

# Load data
df = generate_sample_data()

# Header
st.markdown("""
<div style="background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 1.5rem; margin: -1rem -1rem 2rem -1rem; text-align: center; border-radius: 0 0 10px 10px;">
    <h1 style="margin: 0; color: white;">🌬️ AtmosAnalytics Platform</h1>
    <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Professional Environmental Intelligence & Data Analytics</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Navigation
def render_sidebar():
    with st.sidebar:
        st.header("🧭 Navigation")
        
        pages = {
            'overview': '🏠 Overview',
            'monitoring': '📈 Real-time Monitoring', 
            'analytics': '🔍 Analytics',
            'alerts': '🚨 Alert Management',
            'reports': '📋 Reports & Export',
            'settings': '⚙️ Settings'
        }
        
        for key, label in pages.items():
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state.current_page = key
                st.rerun()
        
        st.divider()
        
        # Filters
        st.header("🔧 Filter Options")
        selected_cities = st.multiselect(
            "Select Cities",
            options=df['city'].unique(),
            default=df['city'].unique()
        )
        
        date_range = st.date_input(
            "Select Date Range",
            value=(df['timestamp'].min(), df['timestamp'].max()),
            min_value=df['timestamp'].min(),
            max_value=df['timestamp'].max()
        )
        
        st.divider()
        
        # Settings
        st.header("⚙️ Quick Settings")
        auto_refresh = st.checkbox("Auto Refresh", value=st.session_state.auto_refresh)
        if auto_refresh != st.session_state.auto_refresh:
            st.session_state.auto_refresh = auto_refresh
        
        refresh_interval = st.selectbox("Refresh Interval", ["5s", "30s", "1m", "5m"], index=1)
        
        return selected_cities, date_range

selected_cities, date_range = render_sidebar()

# Filter data
filtered_df = df[df['city'].isin(selected_cities)]
if len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df['timestamp'].dt.date >= date_range[0]) &
        (filtered_df['timestamp'].dt.date <= date_range[1])
    ]

# Page routing
def render_overview_page():
    st.header("📊 Environmental Intelligence Overview")
    
    # Key metrics - exact same as original
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_aqi = filtered_df['aqi'].mean()
        st.metric("Average AQI", f"{avg_aqi:.0f}",
                 delta="Good" if avg_aqi < 50 else "Moderate" if avg_aqi < 100 else "Poor")
    
    with col2:
        cities = filtered_df['city'].nunique()
        st.metric("Cities Monitored", f"{cities}")
    
    with col3:
        # Mock active alerts
        active_alerts = 3
        st.metric("Active Alerts", f"{active_alerts}",
                 delta="Clear" if active_alerts == 0 else f"{active_alerts} active")
    
    with col4:
        measurements = len(filtered_df)
        st.metric("Data Points", f"{measurements:,}")
    
    st.divider()
    
    # Visualizations - exact same as original
    col1, col2 = st.columns(2)
    
    with col1:
        # AQI Distribution
        fig_hist = px.histogram(filtered_df, x='aqi', nbins=30,
                               title="AQI Distribution",
                               labels={'aqi': 'Air Quality Index', 'count': 'Frequency'})
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        # Cities by AQI
        city_aqi = filtered_df.groupby('city')['aqi'].mean().reset_index()
        city_aqi = city_aqi.sort_values('aqi', ascending=True).head(10)
        
        fig_bar = px.bar(city_aqi, x='aqi', y='city', orientation='h',
                        title="Average AQI by City",
                        color='aqi', color_continuous_scale='RdYlGn_r')
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Time series - exact same as original
    st.subheader("📈 Environmental Quality Trends")
    
    df_time = filtered_df.sort_values('timestamp')
    fig_line = px.line(df_time, x='timestamp', y='aqi', color='city',
                      title="AtmosAnalytics - Air Quality Timeline")
    st.plotly_chart(fig_line, use_container_width=True)
    
    # Data table - exact same as original
    st.subheader("📋 Recent Measurements")
    display_cols = ['city', 'aqi', 'pm2.5', 'pm10', 'timestamp']
    st.dataframe(filtered_df[display_cols].head(20), use_container_width=True, hide_index=True)

def render_monitoring_page():
    st.header("📈 Real-time Monitoring")
    
    # Real-time charts
    fig_aqi = px.line(
        filtered_df,
        x='timestamp',
        y='aqi',
        color='city',
        title='AQI Over Time',
        labels={'aqi': 'Air Quality Index', 'timestamp': 'Date'}
    )
    st.plotly_chart(fig_aqi, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_pm25 = px.box(
            filtered_df,
            x='city',
            y='pm2.5',
            title='PM2.5 Distribution by City',
            labels={'pm2.5': 'PM2.5 (μg/m³)'}
        )
        st.plotly_chart(fig_pm25, use_container_width=True)
    
    with col2:
        latest_data = filtered_df.groupby('city').last().reset_index()
        fig_bar = px.bar(
            latest_data,
            x='city',
            y='aqi',
            color='aqi',
            title='Current AQI by City',
            color_continuous_scale='RdYlGn_r'
        )
        st.plotly_chart(fig_bar, use_container_width=True)

def render_analytics_page():
    st.header("🔍 Advanced Analytics")
    
    # Analysis type selector - exact same as original
    analysis_type = st.selectbox(
        "Select Analysis Type",
        ["Trend Analysis", "Correlation Analysis", "City Comparison", "Pollution Patterns"]
    )
    
    if analysis_type == "Trend Analysis":
        st.subheader("📈 Pollution Trends")
        
        # Trend by pollutant - exact same as original
        pollutants = ['aqi', 'pm2.5', 'pm10', 'temperature', 'humidity']
        selected_pollutant = st.selectbox("Select Pollutant", pollutants)
        
        # Create trend data
        df_trend = filtered_df.groupby('timestamp')[selected_pollutant].mean().reset_index()
        fig = px.line(df_trend, x='timestamp', y=selected_pollutant,
                     title=f"{selected_pollutant.upper()} Trend Over Time")
        st.plotly_chart(fig, use_container_width=True)
    
    elif analysis_type == "Correlation Analysis":
        st.subheader("🔗 Pollutant Correlations")
        
        # Correlation matrix - exact same as original
        corr_cols = ['aqi', 'pm2.5', 'pm10', 'temperature', 'humidity']
        corr_matrix = filtered_df[corr_cols].corr()
        
        fig = px.imshow(corr_matrix, text_auto=True,
                      title="Correlation Matrix",
                      color_continuous_scale='RdBu')
        st.plotly_chart(fig, use_container_width=True)
    
    elif analysis_type == "City Comparison":
        st.subheader("🏙️ City Comparison")
        
        # Select cities to compare - exact same as original
        cities = filtered_df['city'].unique()
        selected_cities_analytics = st.multiselect("Select Cities", cities, default=cities[:3])
        
        if selected_cities_analytics:
            df_cities = filtered_df[filtered_df['city'].isin(selected_cities_analytics)]
            
            # Box plot comparison - exact same as original
            fig = px.box(df_cities, x='city', y='aqi',
                       title="AQI Distribution by City")
            st.plotly_chart(fig, use_container_width=True)
    
    elif analysis_type == "Pollution Patterns":
        st.subheader("🔄 Pollution Patterns")
        
        # Hourly patterns - exact same as original
        filtered_df_copy = filtered_df.copy()
        filtered_df_copy['hour'] = pd.to_datetime(filtered_df_copy['timestamp']).dt.hour
        hourly_pattern = filtered_df_copy.groupby('hour')['aqi'].mean().reset_index()
        
        fig = px.bar(hourly_pattern, x='hour', y='aqi',
                   title="Average AQI by Hour of Day")
        st.plotly_chart(fig, use_container_width=True)

def render_alerts_page():
    st.header("🚨 Alert Management")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Active Alerts")
        
        # Mock alert data
        alerts_data = [
            {"Time": "2 min ago", "City": "Los Angeles", "Severity": "High", "Message": "PM2.5 levels exceed WHO guidelines"},
            {"Time": "15 min ago", "City": "Houston", "Severity": "Medium", "Message": "AQI reaching unhealthy levels"},
            {"Time": "1 hour ago", "City": "Phoenix", "Severity": "Low", "Message": "Temperature above average"}
        ]
        
        for alert in alerts_data:
            severity_color = {"High": "error", "Medium": "warning", "Low": "info"}[alert["Severity"]]
            with st.container():
                st.markdown(f"**{alert['City']}** - {alert['Time']}")
                getattr(st, severity_color)(f"🚨 {alert['Message']}")
    
    with col2:
        st.subheader("⚙️ Alert Settings")
        st.slider("AQI Threshold", 0, 300, 150)
        st.slider("PM2.5 Threshold", 0, 100, 35)
        st.checkbox("Email Notifications", True)
        st.checkbox("SMS Alerts", False)

def render_reports_page():
    st.header("📋 Reports & Export")
    
    report_type = st.selectbox("Report Type", 
                              ["Daily Summary", "Weekly Report", "Monthly Analysis", "Custom Range"])
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Data Export")
        if st.button("Export to CSV"):
            st.success("✅ Data exported successfully!")
        if st.button("Export to Excel"):
            st.success("✅ Excel report generated!")
    
    with col2:
        st.subheader("📈 Report Preview")
        st.dataframe(filtered_df.head(10), use_container_width=True)

def render_settings_page():
    st.header("⚙️ Settings & Configuration")
    
    tabs = st.tabs(["🎨 General", "🚨 Alerts", "📊 Data Sources", "👤 User Profile"])
    
    with tabs[0]:
        st.subheader("General Settings")
        st.selectbox("Theme", ["Light", "Dark", "Auto"])
        st.selectbox("Language", ["English", "Spanish", "French"])
        st.slider("Data Refresh Rate (seconds)", 5, 300, 30)
    
    with tabs[1]:
        st.subheader("Alert Configuration")
        st.checkbox("Enable Email Alerts", True)
        st.text_input("Email Address", "user@example.com")
        st.multiselect("Alert Types", ["AQI", "PM2.5", "Temperature", "Humidity"], default=["AQI"])
    
    with tabs[2]:
        st.subheader("Data Sources")
        st.checkbox("EPA Monitoring Stations", True)
        st.checkbox("Weather API", True)
        st.checkbox("Satellite Data", False)
    
    with tabs[3]:
        st.subheader("User Profile")
        st.text_input("Name", "Administrator")
        st.text_input("Organization", "Environmental Agency")
        st.selectbox("Role", ["Admin", "Analyst", "Viewer"])

# Route to appropriate page
pages = {
    'overview': render_overview_page,
    'monitoring': render_monitoring_page,
    'analytics': render_analytics_page,
    'alerts': render_alerts_page,
    'reports': render_reports_page,
    'settings': render_settings_page
}

current_page = st.session_state.current_page
if current_page in pages:
    pages[current_page]()
else:
    render_overview_page()

# Footer
st.markdown("---")
if st.session_state.auto_refresh:
    st.markdown("🔄 Auto-refresh enabled | 📊 Live environmental data monitoring")
else:
    st.markdown("📊 AtmosAnalytics Platform - Professional Environmental Intelligence")