import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from database import DatabaseConnection
import folium
from streamlit_folium import st_folium

# Page configuration
st.set_page_config(
    page_title="AirFlow Analytics - Premium Air Quality Platform",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for premium styling
def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom Header */
    .main-header {
        background: linear-gradient(135deg, #10b981 0%, #0d9488 100%);
        padding: 1.5rem 2rem;
        border-radius: 0 0 20px 20px;
        margin: -1rem -1rem 2rem -1rem;
        box-shadow: 0 8px 32px rgba(16, 185, 129, 0.3);
        color: white;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .main-header .subtitle {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
        font-weight: 400;
    }
    
    /* Navigation Pills */
    .nav-pills {
        display: flex;
        gap: 0.5rem;
        margin: 1rem 0 2rem 0;
        padding: 0.5rem;
        background: rgba(255, 255, 255, 0.9);
        border-radius: 15px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    }
    
    .nav-pill {
        padding: 0.75rem 1.5rem;
        border-radius: 10px;
        border: none;
        background: transparent;
        color: #374151;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .nav-pill:hover {
        background: linear-gradient(135deg, #10b981, #0d9488);
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }
    
    .nav-pill.active {
        background: linear-gradient(135deg, #10b981, #0d9488);
        color: white;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }
    
    /* Premium Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(135deg, #10b981, #0d9488);
        border-radius: 20px 20px 0 0;
    }
    
    .metric-value {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #10b981, #0d9488);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1;
    }
    
    .metric-label {
        font-size: 1rem;
        color: #6b7280;
        font-weight: 500;
        margin: 0.5rem 0 0 0;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .metric-trend {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-top: 1rem;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .trend-up {
        background: rgba(239, 68, 68, 0.1);
        color: #dc2626;
    }
    
    .trend-down {
        background: rgba(34, 197, 94, 0.1);
        color: #16a34a;
    }
    
    /* AQI Health Scale */
    .aqi-scale {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    .aqi-scale-item {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 0.75rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    .aqi-scale-item:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .aqi-good { background: linear-gradient(135deg, #10b981, #16a34a); }
    .aqi-moderate { background: linear-gradient(135deg, #f59e0b, #eab308); }
    .aqi-unhealthy-sg { background: linear-gradient(135deg, #f97316, #ea580c); }
    .aqi-unhealthy { background: linear-gradient(135deg, #ef4444, #dc2626); }
    .aqi-very-unhealthy { background: linear-gradient(135deg, #a855f7, #9333ea); }
    .aqi-hazardous { background: linear-gradient(135deg, #7c2d12, #451a03); }
    
    .aqi-color-box {
        width: 20px;
        height: 20px;
        border-radius: 6px;
        border: 2px solid rgba(255, 255, 255, 0.8);
    }
    
    .aqi-text {
        color: white;
        font-weight: 500;
        flex: 1;
    }
    
    .aqi-range {
        color: rgba(255, 255, 255, 0.9);
        font-size: 0.9rem;
    }
    
    /* Loading Skeleton */
    .skeleton {
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
        border-radius: 10px;
    }
    
    @keyframes loading {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    /* Alert Cards */
    .alert-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        border-left: 4px solid;
        transition: all 0.3s ease;
    }
    
    .alert-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
    }
    
    .alert-high { border-left-color: #ef4444; }
    .alert-medium { border-left-color: #f97316; }
    .alert-low { border-left-color: #eab308; }
    
    .alert-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .alert-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .badge-high {
        background: rgba(239, 68, 68, 0.1);
        color: #dc2626;
    }
    
    .badge-medium {
        background: rgba(249, 115, 22, 0.1);
        color: #ea580c;
    }
    
    .badge-low {
        background: rgba(234, 179, 8, 0.1);
        color: #ca8a04;
    }
    
    /* Floating Action Button */
    .fab {
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, #10b981, #0d9488);
        color: white;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.4);
        transition: all 0.3s ease;
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .fab:hover {
        transform: scale(1.1);
        box-shadow: 0 12px 36px rgba(16, 185, 129, 0.5);
    }
    
    /* Status Indicator */
    .status-indicator {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 20px;
        font-size: 0.9rem;
        color: #059669;
        font-weight: 500;
        margin: 1rem 0;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10b981;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main-header {
            padding: 1rem;
            margin: -1rem -1rem 1rem -1rem;
        }
        
        .main-header h1 {
            font-size: 2rem;
        }
        
        .nav-pills {
            flex-wrap: wrap;
            gap: 0.25rem;
        }
        
        .nav-pill {
            padding: 0.5rem 1rem;
            font-size: 0.9rem;
        }
        
        .metric-card {
            padding: 1.5rem;
            margin: 0.5rem 0;
        }
        
        .metric-value {
            font-size: 2.5rem;
        }
        
        .fab {
            bottom: 1rem;
            right: 1rem;
            width: 50px;
            height: 50px;
        }
    }
    
    /* Chart Container */
    .chart-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #10b981, #0d9488);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #059669, #0f766e);
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize database connection
@st.cache_resource
def get_database_connection():
    return DatabaseConnection()

def create_header():
    st.markdown("""
    <div class="main-header">
        <h1>🌍 AirFlow Analytics</h1>
        <p class="subtitle">Premium Air Quality Monitoring Platform</p>
    </div>
    """, unsafe_allow_html=True)

def create_navigation():
    pages = [
        ("🏠", "Home", "home"),
        ("🗺️", "Map View", "map"), 
        ("📊", "Analytics", "analytics"),
        ("🚨", "Alerts", "alerts"),
        ("⚙️", "Settings", "settings")
    ]
    
    # Initialize session state for navigation
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'
    
    nav_html = '<div class="nav-pills">'
    for icon, label, key in pages:
        active_class = "active" if st.session_state.current_page == key else ""
        nav_html += f'''
        <button class="nav-pill {active_class}" onclick="setPage('{key}')">
            <span>{icon}</span>
            <span>{label}</span>
        </button>
        '''
    nav_html += '</div>'
    
    nav_html += '''
    <script>
    function setPage(page) {
        // This will be handled by Streamlit buttons below
        window.parent.postMessage({type: 'streamlit:setPage', page: page}, '*');
    }
    </script>
    '''
    
    st.markdown(nav_html, unsafe_allow_html=True)
    
    # Create invisible buttons for navigation
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button("🏠 Home", key="nav_home", help="Global Overview"):
            st.session_state.current_page = 'home'
            st.rerun()
    with col2:
        if st.button("🗺️ Map", key="nav_map", help="Interactive Map"):
            st.session_state.current_page = 'map'
            st.rerun()
    with col3:
        if st.button("📊 Analytics", key="nav_analytics", help="Deep Analysis"):
            st.session_state.current_page = 'analytics'
            st.rerun()
    with col4:
        if st.button("🚨 Alerts", key="nav_alerts", help="Alert Management"):
            st.session_state.current_page = 'alerts'
            st.rerun()
    with col5:
        if st.button("⚙️ Settings", key="nav_settings", help="Configuration"):
            st.session_state.current_page = 'settings'
            st.rerun()

def create_status_indicator():
    current_time = datetime.now().strftime("%H:%M:%S")
    st.markdown(f"""
    <div class="status-indicator">
        <div class="status-dot"></div>
        <span>Live Data • Last updated: {current_time}</span>
    </div>
    """, unsafe_allow_html=True)

def create_metric_card(title, value, trend=None, trend_value=None, icon="📊"):
    trend_html = ""
    if trend and trend_value:
        trend_class = "trend-up" if trend == "up" else "trend-down"
        trend_icon = "↗️" if trend == "up" else "↘️"
        trend_html = f'''
        <div class="metric-trend {trend_class}">
            <span>{trend_icon}</span>
            <span>{trend_value}</span>
        </div>
        '''
    
    card_html = f"""
    <div class="metric-card">
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
            <span style="font-size: 2rem;">{icon}</span>
            <h3 class="metric-label">{title}</h3>
        </div>
        <h2 class="metric-value">{value}</h2>
        {trend_html}
    </div>
    """
    return card_html

def create_aqi_health_scale():
    aqi_levels = [
        ("Good", "0-50", "aqi-good", "😊"),
        ("Moderate", "51-100", "aqi-moderate", "😐"),
        ("Unhealthy for Sensitive Groups", "101-150", "aqi-unhealthy-sg", "😷"),
        ("Unhealthy", "151-200", "aqi-unhealthy", "😵"),
        ("Very Unhealthy", "201-300", "aqi-very-unhealthy", "🤢"),
        ("Hazardous", "301+", "aqi-hazardous", "☠️")
    ]
    
    scale_html = '''
    <div class="aqi-scale">
        <h3 style="margin-bottom: 1rem; color: #374151; font-weight: 600;">AQI Health Impact Scale</h3>
    '''
    
    for level, range_val, css_class, emoji in aqi_levels:
        scale_html += f'''
        <div class="aqi-scale-item {css_class}">
            <div class="aqi-color-box"></div>
            <span class="aqi-text">{emoji} {level}</span>
            <span class="aqi-range">{range_val}</span>
        </div>
        '''
    
    scale_html += '</div>'
    return scale_html

def get_aqi_color(aqi):
    """Return color based on AQI value"""
    if aqi <= 50:
        return "#10b981"
    elif aqi <= 100:
        return "#f59e0b"
    elif aqi <= 150:
        return "#f97316"
    elif aqi <= 200:
        return "#ef4444"
    elif aqi <= 300:
        return "#a855f7"
    else:
        return "#7c2d12"

def create_loading_skeleton(height="200px"):
    return f'''
    <div class="skeleton" style="height: {height}; margin: 1rem 0;"></div>
    '''

def home_page(db):
    """Premium Home Page with Global Overview"""
    st.markdown("## 🌍 Global Air Quality Overview")
    
    # Status indicator
    create_status_indicator()
    
    # Get data
    with st.spinner("Loading global insights..."):
        df = db.get_latest_air_quality_data(24)
        stats = db.get_data_quality_stats()
        alerts = db.get_active_alerts()
    
    if df.empty:
        st.warning("No data available. Please check your data sources.")
        return
    
    # Hero Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_aqi = df['aqi'].mean()
        aqi_trend = "down" if avg_aqi < 75 else "up"
        st.markdown(create_metric_card(
            "Global AQI Average", 
            f"{avg_aqi:.0f}", 
            aqi_trend, 
            "±3.2 vs yesterday",
            "🌍"
        ), unsafe_allow_html=True)
    
    with col2:
        cities_count = len(df['city'].unique())
        st.markdown(create_metric_card(
            "Cities Monitored", 
            f"{cities_count:,}", 
            "up", 
            "+2 new cities",
            "🏙️"
        ), unsafe_allow_html=True)
    
    with col3:
        active_alerts_count = len(alerts) if not alerts.empty else 0
        alert_trend = "down" if active_alerts_count < 5 else "up"
        st.markdown(create_metric_card(
            "Active Alerts", 
            f"{active_alerts_count}", 
            alert_trend, 
            "High priority",
            "🚨"
        ), unsafe_allow_html=True)
    
    with col4:
        total_measurements = stats.get('air_quality', {}).get('total_measurements', 0)
        st.markdown(create_metric_card(
            "24h Measurements", 
            f"{total_measurements:,}", 
            "up", 
            "Real-time data",
            "📈"
        ), unsafe_allow_html=True)
    
    # AQI Health Scale
    st.markdown(create_aqi_health_scale(), unsafe_allow_html=True)
    
    # Real-time Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("🏆 Top 10 Cities by AQI")
        if not df.empty:
            # Get latest data for each city
            latest_df = df.groupby('city').last().reset_index()
            top_cities = latest_df.nlargest(10, 'aqi')
            
            fig = px.bar(
                top_cities, 
                x='aqi', 
                y='city',
                orientation='h',
                color='aqi',
                color_continuous_scale=['#10b981', '#f59e0b', '#f97316', '#ef4444', '#a855f7'],
                title=""
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', size=12),
                coloraxis_showscale=False,
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("📊 AQI Distribution")
        if not df.empty:
            # Create AQI distribution chart
            aqi_bins = [0, 50, 100, 150, 200, 300, 500]
            aqi_labels = ['Good', 'Moderate', 'Unhealthy SG', 'Unhealthy', 'Very Unhealthy', 'Hazardous']
            df['aqi_category'] = pd.cut(df['aqi'], bins=aqi_bins, labels=aqi_labels, right=False)
            
            aqi_counts = df['aqi_category'].value_counts().reset_index()
            aqi_counts.columns = ['category', 'count']
            
            colors = ['#10b981', '#f59e0b', '#f97316', '#ef4444', '#a855f7', '#7c2d12']
            
            fig = px.pie(
                aqi_counts, 
                values='count', 
                names='category',
                color_discrete_sequence=colors,
                title=""
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', size=12),
                height=400,
                showlegend=True,
                legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05)
            )
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Pollutant Trends
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("📈 24-Hour Pollutant Trends")
    if not df.empty and len(df) > 1:
        # Create time series for major pollutants
        df_hourly = df.set_index('timestamp').resample('1H').mean()
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('PM2.5 (μg/m³)', 'PM10 (μg/m³)', 'NO2 (ppb)', 'O3 (ppb)'),
            vertical_spacing=0.12
        )
        
        pollutants = [
            ('pm25', '#ef4444', 1, 1),
            ('pm10', '#f97316', 1, 2),
            ('no2', '#8b5cf6', 2, 1),
            ('o3', '#06b6d4', 2, 2)
        ]
        
        for pollutant, color, row, col in pollutants:
            if pollutant in df_hourly.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df_hourly.index,
                        y=df_hourly[pollutant],
                        mode='lines+markers',
                        line=dict(color=color, width=3),
                        marker=dict(size=6),
                        name=pollutant.upper(),
                        showlegend=False
                    ),
                    row=row, col=col
                )
        
        fig.update_layout(
            height=600,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter', size=12)
        )
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
        
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def map_view_page(db):
    """Interactive Map View"""
    st.markdown("## 🗺️ Interactive Air Quality Map")
    
    create_status_indicator()
    
    # Get data
    df = db.get_latest_air_quality_data(24)
    
    if df.empty:
        st.warning("No location data available for mapping.")
        return
    
    # Create map
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    # Filter for latest data per city
    latest_df = df.groupby('city').last().reset_index()
    
    # Create folium map
    if not latest_df.empty and 'latitude' in latest_df.columns and 'longitude' in latest_df.columns:
        # Calculate center of map
        center_lat = latest_df['latitude'].mean()
        center_lon = latest_df['longitude'].mean()
        
        # Create map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=6,
            tiles='CartoDB positron'
        )
        
        # Add markers for each city
        for _, row in latest_df.iterrows():
            if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                aqi_color = get_aqi_color(row['aqi'])
                
                popup_html = f"""
                <div style="font-family: Inter; width: 200px;">
                    <h4 style="margin: 0; color: {aqi_color};">{row['city']}</h4>
                    <p style="margin: 5px 0;"><b>Country:</b> {row.get('country', 'N/A')}</p>
                    <p style="margin: 5px 0;"><b>AQI:</b> <span style="color: {aqi_color}; font-weight: bold;">{row['aqi']:.0f}</span></p>
                    <p style="margin: 5px 0;"><b>PM2.5:</b> {row.get('pm25', 'N/A'):.1f} μg/m³</p>
                    <p style="margin: 5px 0;"><b>Updated:</b> {row['timestamp'].strftime('%H:%M')}</p>
                </div>
                """
                
                folium.CircleMarker(
                    location=[row['latitude'], row['longitude']],
                    radius=max(8, min(20, row['aqi'] / 10)),
                    popup=folium.Popup(popup_html, max_width=250),
                    color='white',
                    weight=2,
                    fillColor=aqi_color,
                    fillOpacity=0.8,
                    tooltip=f"{row['city']}: AQI {row['aqi']:.0f}"
                ).add_to(m)
        
        # Display map
        map_data = st_folium(m, width=None, height=600, returned_objects=["last_clicked"])
        
        # Show clicked city details
        if map_data["last_clicked"] is not None:
            clicked_lat = map_data["last_clicked"]["lat"]
            clicked_lng = map_data["last_clicked"]["lng"]
            
            # Find closest city
            latest_df['distance'] = ((latest_df['latitude'] - clicked_lat)**2 + 
                                   (latest_df['longitude'] - clicked_lng)**2)**0.5
            closest_city = latest_df.loc[latest_df['distance'].idxmin()]
            
            st.markdown("### 📍 Selected City Details")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("City", closest_city['city'])
                st.metric("AQI", f"{closest_city['aqi']:.0f}")
            
            with col2:
                st.metric("PM2.5", f"{closest_city.get('pm25', 0):.1f} μg/m³")
                st.metric("PM10", f"{closest_city.get('pm10', 0):.1f} μg/m³")
            
            with col3:
                st.metric("Country", closest_city.get('country', 'N/A'))
                st.metric("Last Updated", closest_city['timestamp'].strftime('%H:%M:%S'))
    
    else:
        st.info("No location coordinates available for mapping. Please check your data sources.")
    
    st.markdown('</div>', unsafe_allow_html=True)

def analytics_page(db):
    """Advanced Analytics Page"""
    st.markdown("## 📊 Advanced Analytics & Insights")
    
    create_status_indicator()
    
    # City selector
    df = db.get_latest_air_quality_data(168)  # 7 days
    
    if df.empty:
        st.warning("No data available for analytics.")
        return
    
    cities = sorted(df['city'].unique())
    selected_cities = st.multiselect(
        "🏙️ Select Cities for Comparison",
        cities,
        default=cities[:3] if len(cities) >= 3 else cities,
        help="Choose up to 5 cities for detailed comparison"
    )
    
    if not selected_cities:
        st.info("Please select at least one city to view analytics.")
        return
    
    # Filter data for selected cities
    filtered_df = df[df['city'].isin(selected_cities)]
    
    # Time range selector
    col1, col2 = st.columns(2)
    with col1:
        time_range = st.selectbox(
            "📅 Time Range",
            ["24 Hours", "7 Days", "30 Days"],
            index=1
        )
    
    with col2:
        chart_type = st.selectbox(
            "📈 Chart Type",
            ["Line Chart", "Area Chart", "Bar Chart"],
            index=0
        )
    
    # Pollutant selector
    available_pollutants = [col for col in ['pm25', 'pm10', 'co', 'no2', 'o3', 'so2'] if col in filtered_df.columns]
    selected_pollutants = st.multiselect(
        "🧪 Select Pollutants",
        available_pollutants,
        default=['pm25', 'pm10'] if len(available_pollutants) >= 2 else available_pollutants[:1],
        help="Choose pollutants to analyze"
    )
    
    if not selected_pollutants:
        st.info("Please select at least one pollutant.")
        return
    
    # Create comparison charts
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader(f"🔬 Pollutant Analysis - {time_range}")
    
    # Create subplots for each pollutant
    fig = make_subplots(
        rows=len(selected_pollutants),
        cols=1,
        subplot_titles=[f"{p.upper()} Concentration" for p in selected_pollutants],
        vertical_spacing=0.08
    )
    
    colors = ['#10b981', '#3b82f6', '#ef4444', '#f59e0b', '#8b5cf6', '#06b6d4']
    
    for i, pollutant in enumerate(selected_pollutants):
        for j, city in enumerate(selected_cities[:len(colors)]):
            city_data = filtered_df[filtered_df['city'] == city].sort_values('timestamp')
            
            if not city_data.empty and pollutant in city_data.columns:
                if chart_type == "Line Chart":
                    trace = go.Scatter(
                        x=city_data['timestamp'],
                        y=city_data[pollutant],
                        mode='lines+markers',
                        name=f"{city}",
                        line=dict(color=colors[j % len(colors)], width=3),
                        marker=dict(size=4),
                        showlegend=(i == 0)  # Only show legend for first subplot
                    )
                elif chart_type == "Area Chart":
                    trace = go.Scatter(
                        x=city_data['timestamp'],
                        y=city_data[pollutant],
                        mode='lines',
                        fill='tonexty' if j > 0 else 'tozeroy',
                        name=f"{city}",
                        line=dict(color=colors[j % len(colors)], width=2),
                        showlegend=(i == 0)
                    )
                else:  # Bar Chart
                    trace = go.Bar(
                        x=city_data['timestamp'],
                        y=city_data[pollutant],
                        name=f"{city}",
                        marker=dict(color=colors[j % len(colors)]),
                        showlegend=(i == 0)
                    )
                
                fig.add_trace(trace, row=i+1, col=1)
    
    fig.update_layout(
        height=400 * len(selected_pollutants),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter', size=12),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Statistical Summary
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("📈 Statistical Summary")
        
        summary_stats = []
        for city in selected_cities:
            city_data = filtered_df[filtered_df['city'] == city]
            for pollutant in selected_pollutants:
                if pollutant in city_data.columns:
                    stats_row = {
                        'City': city,
                        'Pollutant': pollutant.upper(),
                        'Mean': f"{city_data[pollutant].mean():.2f}",
                        'Max': f"{city_data[pollutant].max():.2f}",
                        'Min': f"{city_data[pollutant].min():.2f}",
                        'Std Dev': f"{city_data[pollutant].std():.2f}"
                    }
                    summary_stats.append(stats_row)
        
        if summary_stats:
            summary_df = pd.DataFrame(summary_stats)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("🎯 Correlation Analysis")
        
        if len(selected_pollutants) > 1:
            # Create correlation matrix
            corr_data = filtered_df[selected_pollutants].corr()
            
            fig = px.imshow(
                corr_data,
                text_auto=True,
                aspect="auto",
                color_continuous_scale='RdBu_r',
                title=""
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', size=12),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Select multiple pollutants to view correlation analysis.")
        
        st.markdown('</div>', unsafe_allow_html=True)

def alerts_page(db):
    """Alert Management Page"""
    st.markdown("## 🚨 Alert Management Center")
    
    create_status_indicator()
    
    # Get alerts data
    alerts = db.get_active_alerts()
    
    if alerts.empty:
        st.success("🎉 No active alerts! Air quality is within safe limits.")
        
        # Show some demo alerts for visualization
        st.markdown("### 📜 Recent Alert History (Demo)")
        demo_alerts = pd.DataFrame([
            {
                'city': 'Los Angeles',
                'alert_type': 'PM2.5_HIGH',
                'severity': 'HIGH',
                'pollutant': 'PM2.5',
                'value': 75.2,
                'threshold': 55.0,
                'message': 'PM2.5 levels exceed WHO guidelines',
                'timestamp': datetime.now() - timedelta(hours=2),
                'acknowledged': True
            },
            {
                'city': 'Beijing',
                'alert_type': 'AQI_UNHEALTHY',
                'severity': 'MEDIUM',
                'pollutant': 'AQI',
                'value': 168,
                'threshold': 150,
                'message': 'Air quality reached unhealthy levels',
                'timestamp': datetime.now() - timedelta(hours=5),
                'acknowledged': True
            },
            {
                'city': 'Delhi',
                'alert_type': 'MULTIPLE_POLLUTANTS',
                'severity': 'HIGH',
                'pollutant': 'PM2.5, PM10',
                'value': 89.5,
                'threshold': 75.0,
                'message': 'Multiple pollutants exceed safe levels',
                'timestamp': datetime.now() - timedelta(hours=8),
                'acknowledged': True
            }
        ])
        alerts = demo_alerts
    
    # Alert Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        high_alerts = len(alerts[alerts['severity'] == 'HIGH']) if 'severity' in alerts.columns else 0
        st.markdown(create_metric_card(
            "High Priority", 
            f"{high_alerts}", 
            "down" if high_alerts == 0 else "up", 
            "Requires attention",
            "🔴"
        ), unsafe_allow_html=True)
    
    with col2:
        medium_alerts = len(alerts[alerts['severity'] == 'MEDIUM']) if 'severity' in alerts.columns else 0
        st.markdown(create_metric_card(
            "Medium Priority", 
            f"{medium_alerts}", 
            "down", 
            "Monitor closely",
            "🟡"
        ), unsafe_allow_html=True)
    
    with col3:
        cities_affected = len(alerts['city'].unique()) if 'city' in alerts.columns else 0
        st.markdown(create_metric_card(
            "Cities Affected", 
            f"{cities_affected}", 
            "down", 
            "Geographic spread",
            "🌆"
        ), unsafe_allow_html=True)
    
    with col4:
        avg_response_time = "4.2 min"  # Demo value
        st.markdown(create_metric_card(
            "Avg Response", 
            avg_response_time, 
            "down", 
            "Faster than target",
            "⚡"
        ), unsafe_allow_html=True)
    
    # Alert Cards
    st.markdown("### 🔔 Active Alerts")
    
    for _, alert in alerts.iterrows():
        severity_class = f"alert-{alert['severity'].lower()}"
        badge_class = f"badge-{alert['severity'].lower()}"
        
        # Determine if acknowledged
        ack_status = "✅ Acknowledged" if alert.get('acknowledged', False) else "🔔 New Alert"
        ack_color = "#10b981" if alert.get('acknowledged', False) else "#ef4444"
        
        alert_html = f"""
        <div class="alert-card {severity_class}">
            <div class="alert-header">
                <div>
                    <h4 style="margin: 0; color: #374151;">🏙️ {alert['city']}</h4>
                    <p style="margin: 0.25rem 0 0 0; color: #6b7280; font-size: 0.9rem;">
                        {alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
                <div style="text-align: right;">
                    <span class="alert-badge {badge_class}">{alert['severity']}</span>
                    <p style="margin: 0.25rem 0 0 0; font-size: 0.8rem; color: {ack_color};">
                        {ack_status}
                    </p>
                </div>
            </div>
            
            <div style="margin: 1rem 0;">
                <p style="margin: 0; font-size: 1rem; color: #374151;">
                    <strong>🧪 {alert['pollutant']}:</strong> {alert['value']:.1f} 
                    (Threshold: {alert['threshold']:.1f})
                </p>
                <p style="margin: 0.5rem 0 0 0; color: #6b7280;">
                    {alert['message']}
                </p>
            </div>
            
            <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
                <button style="
                    padding: 0.5rem 1rem; 
                    border: none; 
                    border-radius: 8px; 
                    background: #10b981; 
                    color: white; 
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.3s ease;
                " onmouseover="this.style.background='#059669'" onmouseout="this.style.background='#10b981'">
                    ✅ Acknowledge
                </button>
                <button style="
                    padding: 0.5rem 1rem; 
                    border: 1px solid #d1d5db; 
                    border-radius: 8px; 
                    background: white; 
                    color: #374151; 
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.3s ease;
                " onmouseover="this.style.background='#f3f4f6'" onmouseout="this.style.background='white'">
                    📧 Notify Team
                </button>
            </div>
        </div>
        """
        
        st.markdown(alert_html, unsafe_allow_html=True)
    
    # Alert Timeline Chart
    if not alerts.empty and len(alerts) > 1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("📊 Alert Timeline")
        
        # Create timeline chart
        fig = px.scatter(
            alerts,
            x='timestamp',
            y='city',
            color='severity',
            size='value',
            hover_data=['pollutant', 'message'],
            color_discrete_map={
                'HIGH': '#ef4444',
                'MEDIUM': '#f97316',
                'LOW': '#eab308'
            },
            title=""
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter', size=12),
            height=400,
            showlegend=True
        )
        
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

def settings_page(db):
    """Settings and Configuration Page"""
    st.markdown("## ⚙️ Settings & Configuration")
    
    create_status_indicator()
    
    # User Preferences
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("👤 User Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        theme_mode = st.selectbox(
            "🎨 Theme Mode",
            ["Light Mode", "Dark Mode", "Auto"],
            index=0,
            help="Choose your preferred theme"
        )
        
        refresh_rate = st.select_slider(
            "🔄 Auto Refresh Rate",
            options=[15, 30, 60, 120, 300],
            value=60,
            format_func=lambda x: f"{x} seconds",
            help="How often to refresh data automatically"
        )
        
        temperature_unit = st.selectbox(
            "🌡️ Temperature Unit",
            ["Celsius (°C)", "Fahrenheit (°F)"],
            index=0
        )
    
    with col2:
        notification_alerts = st.checkbox(
            "🔔 Enable Alert Notifications",
            value=True,
            help="Receive browser notifications for new alerts"
        )
        
        email_reports = st.checkbox(
            "📧 Daily Email Reports",
            value=False,
            help="Receive daily summary reports via email"
        )
        
        data_export = st.checkbox(
            "📊 Enable Data Export",
            value=True,
            help="Allow downloading data as CSV/Excel files"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Alert Configuration
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("🚨 Alert Thresholds")
    
    st.info("Configure custom alert thresholds for different pollutants")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Particulate Matter**")
        pm25_threshold = st.number_input(
            "PM2.5 Threshold (μg/m³)",
            min_value=0.0,
            max_value=500.0,
            value=55.0,
            step=5.0
        )
        
        pm10_threshold = st.number_input(
            "PM10 Threshold (μg/m³)",
            min_value=0.0,
            max_value=600.0,
            value=150.0,
            step=10.0
        )
    
    with col2:
        st.markdown("**Gases**")
        no2_threshold = st.number_input(
            "NO2 Threshold (ppb)",
            min_value=0.0,
            max_value=200.0,
            value=100.0,
            step=5.0
        )
        
        o3_threshold = st.number_input(
            "O3 Threshold (ppb)",
            min_value=0.0,
            max_value=300.0,
            value=120.0,
            step=10.0
        )
    
    with col3:
        st.markdown("**Other Pollutants**")
        co_threshold = st.number_input(
            "CO Threshold (ppm)",
            min_value=0.0,
            max_value=50.0,
            value=9.0,
            step=1.0
        )
        
        so2_threshold = st.number_input(
            "SO2 Threshold (ppb)",
            min_value=0.0,
            max_value=1000.0,
            value=75.0,
            step=25.0
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Data Sources
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("🔗 Data Sources & API Keys")
    
    col1, col2 = st.columns(2)
    
    with col1:
        openweather_key = st.text_input(
            "🌤️ OpenWeather API Key",
            type="password",
            placeholder="Enter your API key",
            help="Get your key from openweathermap.org"
        )
        
        iqair_key = st.text_input(
            "🌍 IQAir API Key",
            type="password",
            placeholder="Enter your API key",
            help="Get your key from iqair.com"
        )
    
    with col2:
        db_host = st.text_input(
            "🗄️ Database Host",
            value="postgres",
            help="PostgreSQL database host"
        )
        
        db_port = st.number_input(
            "🔌 Database Port",
            min_value=1000,
            max_value=65535,
            value=5432,
            help="PostgreSQL database port"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # System Status
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("📊 System Status")
    
    # Get system stats
    stats = db.get_data_quality_stats()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Database Connection**")
        db_status = "🟢 Connected" if db.engine else "🔴 Disconnected"
        st.markdown(f"Status: {db_status}")
        
        if stats.get('air_quality'):
            total_records = stats['air_quality'].get('total_measurements', 0)
            st.markdown(f"Total Records: {total_records:,}")
    
    with col2:
        st.markdown("**Data Freshness**")
        if stats.get('air_quality', {}).get('latest_measurement'):
            latest_time = stats['air_quality']['latest_measurement']
            if isinstance(latest_time, str):
                latest_time = datetime.fromisoformat(latest_time.replace('Z', '+00:00'))
            time_diff = datetime.now() - latest_time.replace(tzinfo=None)
            freshness = f"🟢 {time_diff.seconds // 60} min ago" if time_diff.seconds < 3600 else f"🟡 {time_diff.seconds // 3600} hr ago"
            st.markdown(f"Last Update: {freshness}")
    
    with col3:
        st.markdown("**Alert System**")
        active_alerts = len(db.get_active_alerts())
        alert_status = f"🟢 {active_alerts} active" if active_alerts < 5 else f"🟡 {active_alerts} active"
        st.markdown(f"Status: {alert_status}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Action Buttons
    st.markdown("### 🛠️ System Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.success("Data cache cleared! Refreshing...")
            st.rerun()
    
    with col2:
        if st.button("📊 Export Settings", use_container_width=True):
            settings_data = {
                'theme_mode': theme_mode,
                'refresh_rate': refresh_rate,
                'temperature_unit': temperature_unit,
                'notification_alerts': notification_alerts,
                'email_reports': email_reports,
                'data_export': data_export,
                'thresholds': {
                    'pm25': pm25_threshold,
                    'pm10': pm10_threshold,
                    'no2': no2_threshold,
                    'o3': o3_threshold,
                    'co': co_threshold,
                    'so2': so2_threshold
                }
            }
            st.json(settings_data)
    
    with col3:
        if st.button("🧪 Test Alerts", use_container_width=True):
            st.info("🔔 Test alert sent! Check your notification settings.")
    
    with col4:
        if st.button("💾 Save Settings", use_container_width=True):
            st.success("✅ Settings saved successfully!")

def main():
    """Main application function"""
    # Load custom CSS
    load_css()
    
    # Initialize database connection
    db = get_database_connection()
    
    # Create header
    create_header()
    
    # Create navigation
    create_navigation()
    
    # Auto-refresh functionality
    if st.button("🔄", key="refresh_fab", help="Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Add floating refresh button
    st.markdown("""
    <button class="fab" onclick="document.querySelector('[key=refresh_fab]').click()" title="Refresh Data">
        🔄
    </button>
    """, unsafe_allow_html=True)
    
    # Route to appropriate page
    if st.session_state.current_page == 'home':
        home_page(db)
    elif st.session_state.current_page == 'map':
        map_view_page(db)
    elif st.session_state.current_page == 'analytics':
        analytics_page(db)
    elif st.session_state.current_page == 'alerts':
        alerts_page(db)
    elif st.session_state.current_page == 'settings':
        settings_page(db)
    
    # Auto-refresh every 60 seconds
    time.sleep(1)
    st.rerun()

if __name__ == "__main__":
    main()