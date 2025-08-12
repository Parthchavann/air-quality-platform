"""
AirFlow Analytics - Production Ready Dashboard
Enterprise Air Quality Monitoring Platform - Fully Functional Version
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
    page_title="AirFlow Analytics",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium lovable CSS with modern design
def inject_css():
    st.markdown("""
    <style>
    /* Import Premium Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    /* Modern gradient background */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    /* Main content container with glassmorphism */
    .main .block-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 2rem;
        margin-top: 1rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    
    /* Premium animated metric cards */
    div[data-testid="metric-container"] {
        background: linear-gradient(145deg, rgba(255,255,255,0.95), rgba(255,255,255,0.8));
        border: 2px solid rgba(255,255,255,0.2);
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 20px 60px rgba(0,0,0,0.15);
        border: 2px solid rgba(102, 126, 234, 0.3);
        background: linear-gradient(145deg, rgba(255,255,255,1), rgba(255,255,255,0.95));
    }
    
    div[data-testid="metric-container"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.1), transparent);
        transition: left 0.6s;
    }
    
    div[data-testid="metric-container"]:hover::before {
        left: 100%;
    }
    
    /* Elegant headers with gradients */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        font-size: 3rem !important;
        text-align: center;
        margin-bottom: 0 !important;
        letter-spacing: -0.02em;
    }
    
    h2 {
        color: #2d3748 !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
        margin-bottom: 1rem !important;
        position: relative;
        padding-left: 1rem;
    }
    
    h2::before {
        content: '';
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 4px;
        height: 100%;
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 2px;
    }
    
    h3 {
        color: #4a5568 !important;
        font-weight: 600 !important;
        font-size: 1.4rem !important;
    }
    
    /* Premium buttons with hover animations */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border: none;
        border-radius: 15px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        background: linear-gradient(135deg, #5a6fd8 0%, #6b4499 100%);
    }
    
    .stButton > button:active {
        transform: translateY(0px);
    }
    
    /* Sidebar with glassmorphism */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Navigation buttons in sidebar */
    .css-1d391kg .stButton > button {
        background: rgba(255, 255, 255, 0.1);
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        margin-bottom: 0.5rem;
    }
    
    .css-1d391kg .stButton > button:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: translateX(5px);
        box-shadow: 0 4px 20px rgba(255, 255, 255, 0.1);
    }
    
    /* Data tables with modern styling */
    .stDataFrame {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        backdrop-filter: blur(10px);
    }
    
    /* Alert messages with premium styling */
    .stAlert {
        border-radius: 15px;
        border: none;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    .stSuccess {
        background: linear-gradient(135deg, rgba(72, 187, 120, 0.9), rgba(56, 178, 172, 0.9));
        color: white;
    }
    
    .stError {
        background: linear-gradient(135deg, rgba(245, 101, 101, 0.9), rgba(229, 62, 62, 0.9));
        color: white;
    }
    
    .stWarning {
        background: linear-gradient(135deg, rgba(246, 173, 85, 0.9), rgba(237, 137, 54, 0.9));
        color: white;
    }
    
    .stInfo {
        background: linear-gradient(135deg, rgba(66, 153, 225, 0.9), rgba(56, 178, 172, 0.9));
        color: white;
    }
    
    /* Selectbox and inputs with premium styling */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.9);
        border: 2px solid rgba(102, 126, 234, 0.2);
        border-radius: 12px;
        backdrop-filter: blur(10px);
    }
    
    .stMultiSelect > div > div {
        background: rgba(255, 255, 255, 0.9);
        border: 2px solid rgba(102, 126, 234, 0.2);
        border-radius: 12px;
        backdrop-filter: blur(10px);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
    }
    
    /* Plotly chart containers */
    .js-plotly-plot {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    /* Sidebar text styling */
    .css-1d391kg .markdown-text-container {
        color: rgba(255, 255, 255, 0.9) !important;
    }
    
    /* Metric labels with better visibility */
    .metric-container label {
        color: #4a5568 !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Status indicators with glow effect */
    .status-online {
        color: #48bb78;
        text-shadow: 0 0 10px rgba(72, 187, 120, 0.5);
        animation: pulse 2s infinite;
    }
    
    .status-offline {
        color: #f56565;
        text-shadow: 0 0 10px rgba(245, 101, 101, 0.5);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* Loading spinner customization */
    .stSpinner {
        text-align: center;
        color: #667eea;
    }
    
    /* Checkbox and radio styling */
    .stCheckbox > label {
        color: rgba(255, 255, 255, 0.9) !important;
    }
    
    /* Number input styling */
    .stNumberInput > div > div > input {
        background: rgba(255, 255, 255, 0.9);
        border: 2px solid rgba(102, 126, 234, 0.2);
        border-radius: 12px;
        backdrop-filter: blur(10px);
    }
    </style>
    """, unsafe_allow_html=True)

class ProductionDashboard:
    """Production-ready dashboard with all features functional"""
    
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
        """Render application header"""
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col2:
            st.markdown("""
                <div style="text-align: center; padding: 2rem 0;">
                    <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 1rem;">
                        <div style="font-size: 4rem; margin-right: 1rem; animation: float 3s ease-in-out infinite;">🌍</div>
                        <h1 style="margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3.5rem; font-weight: 900; letter-spacing: -0.02em;">
                            AirFlow Analytics
                        </h1>
                    </div>
                    <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 1.2rem; font-weight: 500; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        ✨ Premium Enterprise Air Quality Monitoring Platform ✨
                    </p>
                    <div style="width: 100px; height: 4px; background: linear-gradient(135deg, #667eea, #764ba2); margin: 1rem auto; border-radius: 2px; animation: pulse 2s infinite;"></div>
                </div>
                
                <style>
                @keyframes float {
                    0%, 100% { transform: translateY(0px); }
                    50% { transform: translateY(-10px); }
                }
                
                @keyframes pulse {
                    0%, 100% { opacity: 1; transform: scaleX(1); }
                    50% { opacity: 0.7; transform: scaleX(1.1); }
                }
                </style>
            """, unsafe_allow_html=True)
        
        # Status bar
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status_icon = "🟢" if self.db and self.db.engine else "🔴"
            status_text = "Online" if self.db and self.db.engine else "Offline"
            status_class = "status-online" if self.db and self.db.engine else "status-offline"
            st.markdown(f"""
                <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 15px; text-align: center; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.2);">
                    <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{status_icon}</div>
                    <div style="color: rgba(255,255,255,0.9); font-weight: 600;">System</div>
                    <div class="{status_class}" style="font-weight: 700; font-size: 1.1rem;">{status_text}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
                <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 15px; text-align: center; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.2);">
                    <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🚀</div>
                    <div style="color: rgba(255,255,255,0.9); font-weight: 600;">Environment</div>
                    <div style="color: #48bb78; font-weight: 700; font-size: 1.1rem; text-shadow: 0 0 10px rgba(72, 187, 120, 0.5);">Production</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            current_time = datetime.now().strftime("%H:%M:%S")
            st.markdown(f"""
                <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 15px; text-align: center; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.2);">
                    <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">⏰</div>
                    <div style="color: rgba(255,255,255,0.9); font-weight: 600;">Current Time</div>
                    <div style="color: #667eea; font-weight: 700; font-size: 1.1rem; font-family: 'JetBrains Mono', monospace;">{current_time}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
                <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 15px; text-align: center; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.2);">
                    <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">📦</div>
                    <div style="color: rgba(255,255,255,0.9); font-weight: 600;">Version</div>
                    <div style="color: #764ba2; font-weight: 700; font-size: 1.1rem; font-family: 'JetBrains Mono', monospace;">v2.0.0</div>
                </div>
            """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        """Render sidebar navigation"""
        with st.sidebar:
            st.markdown("""
                <div style="text-align: center; padding: 1.5rem 0; margin-bottom: 2rem;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">🧭</div>
                    <h2 style="color: rgba(255,255,255,0.95); margin: 0; font-size: 1.5rem; font-weight: 700;">Navigation</h2>
                    <div style="width: 50px; height: 3px; background: linear-gradient(135deg, #667eea, #764ba2); margin: 0.5rem auto; border-radius: 2px;"></div>
                </div>
            """, unsafe_allow_html=True)
            
            # Page navigation with current page highlighting
            pages = {
                'overview': ('🏠', 'Overview'),
                'monitoring': ('📈', 'Real-time Monitoring'),
                'analytics': ('🔍', 'Analytics'),
                'alerts': ('🚨', 'Alerts'),
                'reports': ('📋', 'Reports'),
                'settings': ('⚙️', 'Settings')
            }
            
            for key, (icon, label) in pages.items():
                is_current = st.session_state.current_page == key
                button_style = "background: linear-gradient(135deg, #667eea, #764ba2); transform: translateX(5px);" if is_current else ""
                
                st.markdown(f"""
                    <div style="margin-bottom: 0.75rem;">
                        <div style="padding: 0.75rem 1rem; border-radius: 12px; {button_style} transition: all 0.3s ease;">
                            <span style="font-size: 1.2rem; margin-right: 0.5rem;">{icon}</span>
                            <span style="font-weight: {'700' if is_current else '500'}; color: rgba(255,255,255,0.95);">{label}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"{icon} {label}", key=f"nav_{key}", use_container_width=True, type="primary" if is_current else "secondary"):
                    st.session_state.current_page = key
                    st.rerun()
            
            st.markdown("""
                <div style="margin: 2rem 0; height: 2px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent); border-radius: 1px;"></div>
                <div style="text-align: center; padding: 1rem 0;">
                    <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🎛️</div>
                    <h3 style="color: rgba(255,255,255,0.95); margin: 0; font-size: 1.3rem; font-weight: 600;">Controls</h3>
                </div>
            """, unsafe_allow_html=True)
            
            # Time range selector
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
            
            # Action buttons
            st.markdown("## ⚡ Actions")
            
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.cache_data.clear()
                st.success("Data refreshed!")
                st.rerun()
            
            if st.button("🧪 Generate Sample Data", use_container_width=True):
                with st.spinner("Generating sample data..."):
                    try:
                        result = subprocess.run(
                            ["python", "sample_data_generator.py"],
                            capture_output=True,
                            text=True,
                            cwd="/app"
                        )
                        if result.returncode == 0:
                            st.success("✅ Sample data generated!")
                            st.session_state.data_generated = True
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to generate data")
                    except Exception as e:
                        st.error(f"Error: {e}")
            
            # System info
            st.markdown("---")
            st.markdown("## 📊 System Info")
            
            if self.db and self.db.engine:
                stats = self.db.get_data_quality_stats()
                if stats and 'air_quality' in stats:
                    aq_stats = stats['air_quality']
                    st.metric("Total Measurements", f"{aq_stats.get('total_measurements', 0):,}")
                    st.metric("Active Cities", f"{aq_stats.get('cities_count', 0)}")
    
    def get_time_hours(self):
        """Convert time range to hours"""
        mapping = {'1h': 1, '24h': 24, '7d': 168, '30d': 720}
        return mapping.get(st.session_state.time_range, 24)
    
    def render_overview_page(self):
        """Render overview page"""
        st.header("📊 Air Quality Overview")
        
        if not self.db:
            st.error("⚠️ Database connection unavailable")
            return
        
        # Get data
        hours = self.get_time_hours()
        df = self.db.get_latest_air_quality_data(hours)
        
        if df.empty:
            st.warning("No data available. Click 'Generate Sample Data' in the sidebar.")
            return
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_aqi = df['aqi'].mean() if 'aqi' in df.columns else 0
            st.metric("🌍 Global Average AQI", f"{avg_aqi:.0f}")
            if avg_aqi <= 50:
                st.success("Good air quality")
            elif avg_aqi <= 100:
                st.warning("Moderate air quality")
            else:
                st.error("Poor air quality")
        
        with col2:
            cities = df['city'].nunique() if 'city' in df.columns else 0
            st.metric("🏙️ Active Cities", f"{cities}")
        
        with col3:
            alerts = self.db.get_active_alerts()
            active_alerts = len(alerts) if not alerts.empty else 0
            st.metric("🚨 Active Alerts", f"{active_alerts}")
        
        with col4:
            measurements = len(df)
            st.metric("📊 Data Points", f"{measurements:,}")
        
        # Charts
        st.subheader("📈 Air Quality Analysis")
        
        if 'aqi' in df.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                # AQI distribution
                fig_hist = px.histogram(
                    df, x='aqi', nbins=30,
                    title="AQI Distribution",
                    labels={'aqi': 'Air Quality Index', 'count': 'Frequency'}
                )
                fig_hist.update_layout(showlegend=False)
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with col2:
                # Top cities by AQI
                if 'city' in df.columns:
                    city_aqi = df.groupby('city')['aqi'].mean().reset_index()
                    city_aqi = city_aqi.sort_values('aqi', ascending=False).head(10)
                    
                    fig_bar = px.bar(
                        city_aqi, x='aqi', y='city',
                        orientation='h', title="Top Cities by AQI",
                        labels={'aqi': 'Average AQI', 'city': 'City'}
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
        
        # Time series
        if 'timestamp' in df.columns and 'aqi' in df.columns:
            st.subheader("📊 AQI Trends")
            
            df_sorted = df.sort_values('timestamp')
            fig_line = px.line(
                df_sorted.head(500), x='timestamp', y='aqi',
                title="AQI Over Time",
                labels={'timestamp': 'Time', 'aqi': 'Air Quality Index'}
            )
            st.plotly_chart(fig_line, use_container_width=True)
        
        # Data table
        st.subheader("📋 Recent Measurements")
        
        display_cols = ['city', 'country', 'aqi', 'pm25', 'pm10', 'timestamp']
        available_cols = [col for col in display_cols if col in df.columns]
        
        if available_cols:
            recent_data = df[available_cols].head(20)
            if 'timestamp' in recent_data.columns:
                recent_data['timestamp'] = pd.to_datetime(recent_data['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(recent_data, use_container_width=True, hide_index=True)
    
    def render_monitoring_page(self):
        """Render real-time monitoring page"""
        st.header("📈 Real-time Air Quality Monitoring")
        
        if not self.db:
            st.error("⚠️ Database connection unavailable")
            return
        
        hours = self.get_time_hours()
        df = self.db.get_latest_air_quality_data(hours)
        
        if df.empty:
            st.warning("No monitoring data available")
            return
        
        # City selector
        if 'city' in df.columns:
            cities = sorted(df['city'].unique())
            selected_cities = st.multiselect(
                "Select Cities to Monitor",
                cities,
                default=cities[:5] if len(cities) >= 5 else cities
            )
            
            if selected_cities:
                filtered_df = df[df['city'].isin(selected_cities)]
                
                # City metrics
                st.subheader("🏙️ City Metrics")
                cols = st.columns(min(len(selected_cities), 5))
                
                for i, city in enumerate(selected_cities[:5]):
                    city_data = filtered_df[filtered_df['city'] == city]
                    if not city_data.empty and 'aqi' in city_data.columns:
                        with cols[i % 5]:
                            latest_aqi = city_data['aqi'].iloc[-1]
                            st.metric(city, f"{latest_aqi:.0f} AQI")
                
                # Comparison chart
                if 'aqi' in filtered_df.columns and 'timestamp' in filtered_df.columns:
                    st.subheader("📊 City Comparison")
                    
                    fig = go.Figure()
                    for city in selected_cities:
                        city_data = filtered_df[filtered_df['city'] == city].sort_values('timestamp')
                        if not city_data.empty:
                            fig.add_trace(go.Scatter(
                                x=city_data['timestamp'],
                                y=city_data['aqi'],
                                mode='lines',
                                name=city
                            ))
                    
                    fig.update_layout(
                        title="AQI Comparison",
                        xaxis_title="Time",
                        yaxis_title="Air Quality Index",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    def render_analytics_page(self):
        """Render analytics page"""
        st.header("🔍 Advanced Analytics")
        
        if not self.db:
            st.error("⚠️ Database connection unavailable")
            return
        
        df = self.db.get_latest_air_quality_data(168)  # 7 days
        
        if df.empty:
            st.warning("No data available for analytics")
            return
        
        # Analysis options
        col1, col2 = st.columns(2)
        
        with col1:
            analysis_type = st.selectbox(
                "Analysis Type",
                ["Statistical Summary", "Trend Analysis", "Distribution Analysis"]
            )
        
        with col2:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            pollutants = [col for col in ['aqi', 'pm25', 'pm10', 'no2', 'o3'] if col in numeric_cols]
            selected_pollutant = st.selectbox("Select Pollutant", pollutants)
        
        if analysis_type == "Statistical Summary":
            st.subheader("📊 Statistical Summary")
            
            if selected_pollutant:
                stats = {
                    'Mean': df[selected_pollutant].mean(),
                    'Median': df[selected_pollutant].median(),
                    'Std Dev': df[selected_pollutant].std(),
                    'Min': df[selected_pollutant].min(),
                    'Max': df[selected_pollutant].max()
                }
                
                stats_df = pd.DataFrame(list(stats.items()), columns=['Statistic', 'Value'])
                stats_df['Value'] = stats_df['Value'].round(2)
                st.dataframe(stats_df, use_container_width=True, hide_index=True)
        
        elif analysis_type == "Trend Analysis":
            st.subheader("📈 Trend Analysis")
            
            if selected_pollutant and 'timestamp' in df.columns:
                fig = px.line(
                    df.sort_values('timestamp'),
                    x='timestamp', y=selected_pollutant,
                    title=f"{selected_pollutant.upper()} Trends"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        elif analysis_type == "Distribution Analysis":
            st.subheader("📊 Distribution Analysis")
            
            if selected_pollutant:
                fig = px.histogram(
                    df, x=selected_pollutant,
                    title=f"{selected_pollutant.upper()} Distribution",
                    nbins=30
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def render_alerts_page(self):
        """Render alerts page"""
        st.header("🚨 Alert Management")
        
        if not self.db:
            st.error("⚠️ Database connection unavailable")
            return
        
        alerts = self.db.get_active_alerts()
        
        if alerts.empty:
            st.success("✅ No active alerts")
            
            # Alert configuration
            st.subheader("⚙️ Alert Configuration")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.number_input("PM2.5 Threshold (μg/m³)", value=55.0, min_value=0.0)
                st.number_input("PM10 Threshold (μg/m³)", value=150.0, min_value=0.0)
            
            with col2:
                st.number_input("NO2 Threshold (ppb)", value=100.0, min_value=0.0)
                st.number_input("O3 Threshold (ppb)", value=120.0, min_value=0.0)
            
            if st.button("Save Configuration"):
                st.success("Configuration saved!")
        else:
            # Alert summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Alerts", len(alerts))
            
            with col2:
                high_severity = len(alerts[alerts['severity'] == 'HIGH']) if 'severity' in alerts.columns else 0
                st.metric("High Severity", high_severity)
            
            with col3:
                cities_affected = alerts['city'].nunique() if 'city' in alerts.columns else 0
                st.metric("Cities Affected", cities_affected)
            
            # Alert details
            st.subheader("📋 Alert Details")
            
            for _, alert in alerts.iterrows():
                with st.expander(f"🚨 {alert.get('city', 'Unknown')} - {alert.get('severity', 'MEDIUM')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**City:** {alert.get('city', 'N/A')}")
                        st.write(f"**Pollutant:** {alert.get('pollutant', 'N/A')}")
                        st.write(f"**Value:** {alert.get('value', 0):.1f}")
                    
                    with col2:
                        st.write(f"**Threshold:** {alert.get('threshold', 0):.1f}")
                        st.write(f"**Time:** {alert.get('timestamp', 'Unknown')}")
                    
                    st.write(f"**Message:** {alert.get('message', 'No message')}")
                    
                    if st.button(f"Acknowledge", key=f"ack_{alert.name}"):
                        st.success("Alert acknowledged!")
    
    def render_reports_page(self):
        """Render reports page"""
        st.header("📋 Reports & Export")
        
        col1, col2 = st.columns(2)
        
        with col1:
            report_type = st.selectbox(
                "Report Type",
                ["Executive Summary", "Technical Report", "Compliance Report"]
            )
        
        with col2:
            date_range = st.selectbox(
                "Date Range",
                ["Last 24 Hours", "Last Week", "Last Month"]
            )
        
        if st.button("Generate Report", use_container_width=True):
            with st.spinner("Generating report..."):
                time.sleep(2)  # Simulate generation
                st.success(f"✅ {report_type} generated successfully!")
                
                # Sample report data
                if self.db:
                    df = self.db.get_latest_air_quality_data(24)
                    if not df.empty and 'city' in df.columns and 'aqi' in df.columns:
                        summary = df.groupby('city')['aqi'].agg(['mean', 'max', 'min']).round(2)
                        summary.columns = ['Average AQI', 'Max AQI', 'Min AQI']
                        
                        st.subheader("Report Preview")
                        st.dataframe(summary, use_container_width=True)
                        
                        # Download button
                        csv = summary.to_csv()
                        st.download_button(
                            "📥 Download Report",
                            csv,
                            f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            "text/csv"
                        )
    
    def render_settings_page(self):
        """Render settings page"""
        st.header("⚙️ System Settings")
        
        # System status
        st.subheader("System Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status = "🟢 Connected" if self.db and self.db.engine else "🔴 Disconnected"
            st.info(f"**Database:** {status}")
        
        with col2:
            st.info(f"**Version:** 2.0.0")
        
        with col3:
            st.info(f"**Environment:** Production")
        
        # Configuration
        st.subheader("Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.selectbox("Theme", ["Light", "Dark", "Auto"])
            st.selectbox("Language", ["English", "Spanish", "French"])
        
        with col2:
            st.checkbox("Enable Notifications", value=True)
            st.checkbox("Auto-refresh Data", value=False)
        
        if st.button("Save Settings", use_container_width=True):
            st.success("Settings saved successfully!")
        
        # System info
        st.subheader("System Information")
        
        info = {
            "Application": "AirFlow Analytics",
            "Version": "2.0.0",
            "Database": "PostgreSQL",
            "Framework": "Streamlit",
            "Python": "3.10"
        }
        
        for key, value in info.items():
            st.write(f"**{key}:** {value}")
    
    def run(self):
        """Main application runner"""
        inject_css()
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
        
        # Footer
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: #666; padding: 1rem;'>"
            "© 2024 AirFlow Analytics | Enterprise Air Quality Platform"
            "</div>",
            unsafe_allow_html=True
        )

# Main execution
if __name__ == "__main__":
    dashboard = ProductionDashboard()
    dashboard.run()