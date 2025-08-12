"""
Air Quality Monitoring Dashboard - Clean & Professional
Enhanced visibility and improved user experience
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
    page_title="Air Quality Monitor",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean, Professional CSS with High Visibility
def inject_clean_css():
    st.markdown("""
    <style>
    /* Import Professional Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Roboto+Mono:wght@400;500&display=swap');
    
    /* Light Theme for Better Visibility */
    :root {
        --primary: #2563eb;
        --primary-dark: #1e40af;
        --secondary: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --success: #22c55e;
        
        --bg-primary: #ffffff;
        --bg-secondary: #f8fafc;
        --bg-card: #ffffff;
        
        --text-primary: #1e293b;
        --text-secondary: #475569;
        --text-muted: #94a3b8;
        
        --border: #e2e8f0;
        --shadow: rgba(0, 0, 0, 0.05);
        --shadow-hover: rgba(0, 0, 0, 0.1);
    }
    
    /* Main App Background */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: linear-gradient(180deg, #f0f9ff 0%, #ffffff 100%);
        color: var(--text-primary);
    }
    
    /* Container Styling */
    .main .block-container {
        max-width: 1400px;
        padding: 2rem;
        margin: 0 auto;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu, footer, .stDeployButton {
        visibility: hidden;
    }
    
    /* Headers */
    h1 {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        font-size: 2.5rem !important;
        margin-bottom: 0.5rem !important;
        letter-spacing: -0.02em;
    }
    
    h2 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        font-size: 1.75rem !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
    }
    
    h3 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        font-size: 1.25rem !important;
        margin-bottom: 0.75rem !important;
    }
    
    /* Metric Cards */
    div[data-testid="metric-container"] {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px var(--shadow);
        transition: all 0.2s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        box-shadow: 0 4px 12px var(--shadow-hover);
        transform: translateY(-2px);
    }
    
    div[data-testid="metric-container"] label {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    div[data-testid="metric-container"] > div[data-testid="metric-container-value"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: var(--primary) !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.625rem 1.25rem !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px var(--shadow) !important;
    }
    
    .stButton > button:hover {
        background: var(--primary-dark) !important;
        box-shadow: 0 4px 12px var(--shadow-hover) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border) !important;
    }
    
    section[data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        width: 100%;
        text-align: left;
        margin-bottom: 0.5rem;
    }
    
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: var(--bg-card) !important;
        border-color: var(--primary) !important;
        color: var(--primary) !important;
    }
    
    /* Select Boxes */
    .stSelectbox > div > div {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
    }
    
    /* Data Tables */
    .stDataFrame {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }
    
    .stDataFrame tbody tr:hover {
        background: var(--bg-secondary) !important;
    }
    
    /* Alerts */
    .stAlert {
        border-radius: 8px !important;
        border-left: 4px solid !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
    }
    
    .stSuccess {
        background: #f0fdf4 !important;
        border-left-color: var(--success) !important;
        color: #166534 !important;
    }
    
    .stError {
        background: #fef2f2 !important;
        border-left-color: var(--danger) !important;
        color: #991b1b !important;
    }
    
    .stWarning {
        background: #fffbeb !important;
        border-left-color: var(--warning) !important;
        color: #92400e !important;
    }
    
    .stInfo {
        background: #eff6ff !important;
        border-left-color: var(--primary) !important;
        color: #1e40af !important;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: var(--bg-card) !important;
        border-color: var(--primary) !important;
    }
    
    /* Charts */
    .js-plotly-plot {
        border-radius: 8px !important;
        overflow: hidden !important;
        box-shadow: 0 1px 3px var(--shadow) !important;
    }
    
    /* Custom Card Component */
    .custom-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px var(--shadow);
        transition: box-shadow 0.2s ease;
    }
    
    .custom-card:hover {
        box-shadow: 0 4px 12px var(--shadow-hover);
    }
    
    /* Status Badge */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .status-online {
        background: #dcfce7;
        color: #166534;
    }
    
    .status-offline {
        background: #fee2e2;
        color: #991b1b;
    }
    
    /* Loading States */
    .stSpinner {
        color: var(--primary) !important;
    }
    
    /* Improved Typography */
    p {
        color: var(--text-secondary);
        line-height: 1.6;
    }
    
    /* Section Dividers */
    hr {
        border: none;
        border-top: 1px solid var(--border);
        margin: 2rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

class CleanDashboard:
    """Clean and Professional Air Quality Dashboard"""
    
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
        """Render clean header"""
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
                <div style="text-align: center; padding: 2rem 0;">
                    <h1 style="margin: 0; color: #1e293b;">
                        🌍 Air Quality Monitor
                    </h1>
                    <p style="margin: 0.5rem 0 0 0; color: #64748b; font-size: 1.125rem;">
                        Real-time Environmental Intelligence Platform
                    </p>
                </div>
            """, unsafe_allow_html=True)
        
        # Status Row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status = "Online" if self.db and self.db.engine else "Offline"
            st.metric("System Status", status)
        
        with col2:
            st.metric("Environment", "Production")
        
        with col3:
            current_time = datetime.now().strftime("%H:%M:%S")
            st.metric("Last Update", current_time)
        
        with col4:
            st.metric("Version", "v3.0.0")

    def render_sidebar(self):
        """Render clean sidebar navigation"""
        with st.sidebar:
            st.header("🧭 Navigation")
            
            # Navigation
            pages = {
                'overview': ('🏠', 'Overview'),
                'monitoring': ('📈', 'Real-time Monitoring'),
                'analytics': ('🔍', 'Analytics'),
                'alerts': ('🚨', 'Alerts'),
                'reports': ('📋', 'Reports'),
                'settings': ('⚙️', 'Settings')
            }
            
            for key, (icon, label) in pages.items():
                if st.button(f"{icon} {label}", key=f"nav_{key}", use_container_width=True):
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
                
                stats = self.db.get_data_quality_stats()
                if stats and 'air_quality' in stats:
                    aq_stats = stats['air_quality']
                    
                    measurements = aq_stats.get('total_measurements', 0)
                    cities = aq_stats.get('cities_count', 0)
                    
                    st.metric("Total Measurements", f"{measurements:,}")
                    st.metric("Active Cities", f"{cities}")
                else:
                    st.info("No data statistics available")
            else:
                st.divider()
                st.warning("Database not connected")

    def get_time_hours(self):
        """Convert time range to hours"""
        mapping = {'1h': 1, '24h': 24, '7d': 168, '30d': 720}
        return mapping.get(st.session_state.time_range, 24)
    
    def render_overview_page(self):
        """Render overview page with clean design"""
        st.header("Air Quality Overview")
        
        if not self.db:
            st.error("⚠️ Database connection failed. Please check your configuration.")
            return
        
        hours = self.get_time_hours()
        df = self.db.get_latest_air_quality_data(hours)
        
        if df.empty:
            st.warning("No data available. Click 'Generate' in the sidebar to create sample data.")
            return
        
        # Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        if 'aqi' in df.columns:
            avg_aqi = df['aqi'].mean()
            with col1:
                st.metric(
                    label="Average AQI",
                    value=f"{avg_aqi:.0f}",
                    delta="Good" if avg_aqi <= 50 else "Moderate" if avg_aqi <= 100 else "Poor"
                )
        
        if 'city' in df.columns:
            cities = df['city'].nunique()
            with col2:
                st.metric(
                    label="Cities Monitored",
                    value=f"{cities}"
                )
        
        alerts = self.db.get_active_alerts()
        active_alerts = len(alerts) if not alerts.empty else 0
        with col3:
            st.metric(
                label="Active Alerts",
                value=f"{active_alerts}",
                delta="Clear" if active_alerts == 0 else f"{active_alerts} active"
            )
        
        measurements = len(df)
        with col4:
            st.metric(
                label="Data Points",
                value=f"{measurements:,}"
            )
        
        # Charts Section
        st.markdown("<hr>", unsafe_allow_html=True)
        st.subheader("📈 Data Visualizations")
        
        if 'aqi' in df.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                # AQI Distribution
                fig_hist = px.histogram(
                    df, x='aqi', nbins=30,
                    title="AQI Distribution",
                    labels={'aqi': 'Air Quality Index', 'count': 'Frequency'},
                    color_discrete_sequence=['#2563eb']
                )
                fig_hist.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font=dict(family="Inter", color='#1e293b'),
                    title_font=dict(size=16),
                    showlegend=False,
                    xaxis=dict(gridcolor='#e2e8f0'),
                    yaxis=dict(gridcolor='#e2e8f0')
                )
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
                        color_continuous_scale=['#22c55e', '#f59e0b', '#ef4444']
                    )
                    fig_bar.update_layout(
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        font=dict(family="Inter", color='#1e293b'),
                        title_font=dict(size=16),
                        showlegend=False,
                        xaxis=dict(gridcolor='#e2e8f0'),
                        yaxis=dict(gridcolor='#e2e8f0')
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
        
        # Time Series
        if 'timestamp' in df.columns and 'aqi' in df.columns:
            st.subheader("📊 AQI Trend Over Time")
            
            df_sorted = df.sort_values('timestamp')
            fig_line = px.line(
                df_sorted.head(500), x='timestamp', y='aqi',
                title="Air Quality Index Timeline",
                labels={'timestamp': 'Time', 'aqi': 'AQI'},
                color_discrete_sequence=['#2563eb']
            )
            fig_line.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family="Inter", color='#1e293b'),
                title_font=dict(size=16),
                showlegend=False,
                xaxis=dict(gridcolor='#e2e8f0'),
                yaxis=dict(gridcolor='#e2e8f0'),
                hovermode='x unified'
            )
            fig_line.update_traces(line=dict(width=2))
            st.plotly_chart(fig_line, use_container_width=True)
        
        # Data Table
        st.subheader("📋 Recent Measurements")
        
        display_cols = ['city', 'country', 'aqi', 'pm25', 'pm10', 'timestamp']
        available_cols = [col for col in display_cols if col in df.columns]
        
        if available_cols:
            recent_data = df[available_cols].head(20)
            if 'timestamp' in recent_data.columns:
                recent_data['timestamp'] = pd.to_datetime(recent_data['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Style the dataframe
            st.dataframe(
                recent_data,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "aqi": st.column_config.NumberColumn(
                        "AQI",
                        format="%.0f",
                    ),
                    "pm25": st.column_config.NumberColumn(
                        "PM2.5",
                        format="%.1f μg/m³",
                    ),
                    "pm10": st.column_config.NumberColumn(
                        "PM10",
                        format="%.1f μg/m³",
                    ),
                }
            )

    def run(self):
        """Launch the dashboard"""
        inject_clean_css()
        self.render_header()
        self.render_sidebar()
        
        # Page routing
        pages = {
            'overview': self.render_overview_page,
            'monitoring': self.render_overview_page,  # Placeholder
            'analytics': self.render_overview_page,   # Placeholder
            'alerts': self.render_overview_page,      # Placeholder
            'reports': self.render_overview_page,     # Placeholder
            'settings': self.render_overview_page     # Placeholder
        }
        
        current_page = st.session_state.current_page
        if current_page in pages:
            pages[current_page]()
        else:
            st.error("Page not found")
        
        # Footer
        st.markdown("""
            <hr style="margin-top: 3rem;">
            <div style="text-align: center; padding: 2rem 0; color: #64748b;">
                <p style="margin: 0;">© 2024 Air Quality Monitoring Platform | Real-time Environmental Intelligence</p>
            </div>
        """, unsafe_allow_html=True)

# Main execution
if __name__ == "__main__":
    dashboard = CleanDashboard()
    dashboard.run()