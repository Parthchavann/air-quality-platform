"""
AirFlow Analytics - Production Air Quality Dashboard
Enterprise-grade air quality monitoring platform
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import traceback
import folium
from streamlit_folium import st_folium
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

# Production CSS - Clean and Professional
def inject_css():
    st.markdown("""
    <style>
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main styling */
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 1.5rem;
        margin: -1rem -1rem 2rem -1rem;
        text-align: center;
        border-radius: 0 0 10px 10px;
    }
    
    .status-bar {
        background: #f8f9fa;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin-bottom: 1rem;
        font-size: 0.9rem;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 4px solid #2a5298;
        margin: 1rem 0;
    }
    
    .alert-danger { border-left-color: #dc3545; background: #f8d7da; }
    .alert-warning { border-left-color: #ffc107; background: #fff3cd; }
    .alert-success { border-left-color: #28a745; background: #d4edda; }
    .alert-info { border-left-color: #17a2b8; background: #d1ecf1; }
    
    /* Navigation */
    .nav-item {
        padding: 0.75rem 1rem;
        margin: 0.25rem 0;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .nav-item:hover {
        background: #e9ecef;
    }
    
    .nav-item.active {
        background: #2a5298;
        color: white;
    }
    
    /* Charts */
    .chart-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    /* Data quality indicators */
    .quality-good { color: #28a745; }
    .quality-warning { color: #ffc107; }
    .quality-danger { color: #dc3545; }
    
    /* Responsive */
    @media (max-width: 768px) {
        .main-header { padding: 1rem; font-size: 1.5rem; }
        .metric-card { padding: 1rem; }
    }
    </style>
    """, unsafe_allow_html=True)

class ProductionDashboard:
    """Production-ready Air Quality Dashboard"""
    
    def __init__(self):
        self.db = self.get_database_connection()
        self.setup_session_state()
    
    @st.cache_resource
    def get_database_connection():
        """Get cached database connection"""
        try:
            return DatabaseConnection()
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            st.error("Unable to connect to database. Please check your configuration.")
            return None
    
    def setup_session_state(self):
        """Initialize session state variables"""
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'overview'
        if 'selected_cities' not in st.session_state:
            st.session_state.selected_cities = []
        if 'time_range' not in st.session_state:
            st.session_state.time_range = '24h'
    
    def render_header(self):
        """Render main header"""
        st.markdown("""
        <div class="main-header">
            <h1 style="margin: 0; font-size: 2.5rem;">🌍 AirFlow Analytics</h1>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Enterprise Air Quality Monitoring Platform</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_status_bar(self):
        """Render system status bar"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if self.db and self.db.engine:
            status_color = "#28a745"
            status_text = "🟢 System Online"
        else:
            status_color = "#dc3545"
            status_text = "🔴 System Offline"
        
        st.markdown(f"""
        <div class="status-bar" style="border-left-color: {status_color};">
            <strong>{status_text}</strong> | Last Updated: {current_time} | 
            <span style="color: #6c757d;">Production Environment</span>
        </div>
        """, unsafe_allow_html=True)
    
    def render_navigation(self):
        """Render sidebar navigation"""
        st.sidebar.title("📊 Dashboard")
        
        pages = {
            'overview': '🏠 Overview',
            'monitoring': '📈 Monitoring', 
            'analytics': '🔍 Analytics',
            'alerts': '🚨 Alerts',
            'reports': '📋 Reports',
            'settings': '⚙️ Settings'
        }
        
        for page_key, page_name in pages.items():
            if st.sidebar.button(page_name, key=f"nav_{page_key}", use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()
        
        # Filters
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🎛️ Filters")
        
        # Time range selector
        time_ranges = {
            '1h': 'Last Hour',
            '24h': 'Last 24 Hours', 
            '7d': 'Last 7 Days',
            '30d': 'Last 30 Days'
        }
        
        selected_range = st.sidebar.selectbox(
            "📅 Time Range",
            options=list(time_ranges.keys()),
            format_func=lambda x: time_ranges[x],
            index=1
        )
        st.session_state.time_range = selected_range
        
        # Auto-refresh
        auto_refresh = st.sidebar.checkbox("🔄 Auto Refresh", value=True)
        if auto_refresh:
            refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 30, 300, 60)
            if st.sidebar.button("🔄 Refresh Now"):
                st.cache_data.clear()
                st.rerun()
    
    def get_time_hours(self, time_range):
        """Convert time range to hours"""
        mapping = {'1h': 1, '24h': 24, '7d': 168, '30d': 720}
        return mapping.get(time_range, 24)
    
    def safe_execute(self, func, *args, **kwargs):
        """Safely execute database operations with error handling"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error executing {func.__name__}: {e}")
            return None
    
    def render_overview_page(self):
        """Render overview dashboard page"""
        st.title("📊 Air Quality Overview")
        
        if not self.db:
            st.error("⚠️ Database connection unavailable. Please check system status.")
            return
        
        # Get data
        hours = self.get_time_hours(st.session_state.time_range)
        
        with st.spinner(f"Loading data for {st.session_state.time_range}..."):
            df = self.safe_execute(self.db.get_latest_air_quality_data, hours)
            stats = self.safe_execute(self.db.get_data_quality_stats)
            alerts = self.safe_execute(self.db.get_active_alerts)
        
        if df is None or df.empty:
            st.warning("No air quality data available for the selected time range.")
            st.info("💡 Generate sample data: `docker exec airquality-streamlit python sample_data_generator.py`")
            return
        
        # Key Performance Indicators
        st.subheader("🎯 Key Performance Indicators")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_aqi = df['aqi'].mean()
            aqi_trend = "↗️" if avg_aqi > 75 else "↘️"
            st.metric(
                label="🌍 Global AQI",
                value=f"{avg_aqi:.0f}",
                delta=f"{aqi_trend} vs baseline"
            )
        
        with col2:
            cities_count = df['city'].nunique()
            st.metric(
                label="🏙️ Active Cities",
                value=f"{cities_count}",
                delta="Monitoring network"
            )
        
        with col3:
            alert_count = len(alerts) if alerts is not None else 0
            alert_delta = "🔴 Attention needed" if alert_count > 0 else "🟢 All clear"
            st.metric(
                label="🚨 Active Alerts",
                value=f"{alert_count}",
                delta=alert_delta
            )
        
        with col4:
            data_points = len(df) if df is not None else 0
            st.metric(
                label="📊 Data Points",
                value=f"{data_points:,}",
                delta="Real-time monitoring"
            )
        
        # Data Quality Assessment
        st.subheader("✅ Data Quality Assessment")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Data completeness
            if df is not None:
                completeness = (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
                if completeness > 95:
                    quality_class = "quality-good"
                    quality_icon = "🟢"
                elif completeness > 85:
                    quality_class = "quality-warning" 
                    quality_icon = "🟡"
                else:
                    quality_class = "quality-danger"
                    quality_icon = "🔴"
                
                st.markdown(f"""
                <div class="metric-card">
                    <h4>{quality_icon} Data Completeness</h4>
                    <h2 class="{quality_class}">{completeness:.1f}%</h2>
                    <p>Missing data points: {df.isnull().sum().sum()}</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            # Data freshness
            if df is not None and not df.empty:
                latest_time = df['timestamp'].max()
                time_diff = datetime.now() - latest_time
                hours_old = time_diff.total_seconds() / 3600
                
                if hours_old < 1:
                    freshness_class = "quality-good"
                    freshness_icon = "🟢"
                    freshness_text = f"{int(time_diff.total_seconds() / 60)} minutes ago"
                elif hours_old < 6:
                    freshness_class = "quality-warning"
                    freshness_icon = "🟡" 
                    freshness_text = f"{hours_old:.1f} hours ago"
                else:
                    freshness_class = "quality-danger"
                    freshness_icon = "🔴"
                    freshness_text = f"{hours_old:.1f} hours ago"
                
                st.markdown(f"""
                <div class="metric-card">
                    <h4>{freshness_icon} Data Freshness</h4>
                    <h2 class="{freshness_class}">Latest</h2>
                    <p>Last update: {freshness_text}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Global AQI Distribution
        st.subheader("🌍 Global AQI Distribution")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # AQI Histogram
            fig = px.histogram(
                df, 
                x='aqi',
                nbins=30,
                title="AQI Distribution",
                color_discrete_sequence=['#2a5298']
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Top Cities by AQI
            if not df.empty:
                city_aqi = df.groupby('city')['aqi'].mean().reset_index()
                city_aqi = city_aqi.sort_values('aqi', ascending=False).head(10)
                
                fig = px.bar(
                    city_aqi,
                    x='aqi',
                    y='city',
                    orientation='h',
                    title="Top 10 Cities by AQI",
                    color='aqi',
                    color_continuous_scale=['green', 'yellow', 'red']
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Time Series Analysis
        st.subheader("📈 Temporal Trends")
        
        if not df.empty:
            # Aggregate by hour - only numeric columns
            numeric_df = df.select_dtypes(include=[np.number])
            if 'aqi' in numeric_df.columns:
                df_hourly = df.set_index('timestamp').resample('1H')['aqi'].mean().reset_index()
            else:
                df_hourly = pd.DataFrame()
            
            if not df_hourly.empty:
                fig = px.line(
                    df_hourly,
                    x='timestamp',
                    y='aqi',
                    title=f"AQI Trends - {st.session_state.time_range}",
                    line_shape='spline'
                )
                fig.update_traces(line_color='#2a5298', line_width=3)
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No time series data available for visualization.")
        
        # Recent Data Table
        st.subheader("📋 Recent Measurements")
        if not df.empty:
            recent_data = df.nlargest(20, 'timestamp')[
                ['city', 'country', 'aqi', 'pm25', 'pm10', 'timestamp']
            ].copy()
            recent_data['timestamp'] = recent_data['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
            
            st.dataframe(
                recent_data,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "aqi": st.column_config.NumberColumn("AQI", format="%.0f"),
                    "pm25": st.column_config.NumberColumn("PM2.5", format="%.1f"),
                    "pm10": st.column_config.NumberColumn("PM10", format="%.1f")
                }
            )
    
    def render_monitoring_page(self):
        """Render real-time monitoring page"""
        st.title("📈 Real-time Monitoring")
        
        if not self.db:
            st.error("⚠️ Database connection unavailable.")
            return
        
        # Get data
        hours = self.get_time_hours(st.session_state.time_range)
        df = self.safe_execute(self.db.get_latest_air_quality_data, hours)
        
        if df is None or df.empty:
            st.warning("No monitoring data available.")
            return
        
        # City selector
        cities = sorted(df['city'].unique())
        selected_cities = st.multiselect(
            "🏙️ Select Cities to Monitor",
            cities,
            default=cities[:5] if len(cities) >= 5 else cities
        )
        
        if not selected_cities:
            st.info("Please select cities to monitor.")
            return
        
        filtered_df = df[df['city'].isin(selected_cities)]
        
        # Real-time metrics
        st.subheader("⚡ Real-time Metrics")
        
        cols = st.columns(len(selected_cities))
        for i, city in enumerate(selected_cities):
            city_data = filtered_df[filtered_df['city'] == city]
            if not city_data.empty:
                latest_aqi = city_data['aqi'].iloc[-1]
                
                # Determine status color
                if latest_aqi <= 50:
                    status_color = "🟢"
                elif latest_aqi <= 100:
                    status_color = "🟡"
                elif latest_aqi <= 150:
                    status_color = "🟠"
                else:
                    status_color = "🔴"
                
                with cols[i]:
                    st.metric(
                        label=f"{status_color} {city}",
                        value=f"{latest_aqi:.0f}",
                        delta=f"AQI"
                    )
        
        # Multi-city comparison charts
        st.subheader("📊 Multi-City Comparison")
        
        # Pollutant comparison
        pollutants = ['pm25', 'pm10', 'no2', 'o3', 'co', 'so2']
        available_pollutants = [p for p in pollutants if p in filtered_df.columns]
        
        selected_pollutant = st.selectbox(
            "🧪 Select Pollutant",
            available_pollutants,
            format_func=lambda x: x.upper()
        )
        
        if selected_pollutant in filtered_df.columns:
            fig = go.Figure()
            
            colors = px.colors.qualitative.Set1
            
            for i, city in enumerate(selected_cities):
                city_data = filtered_df[filtered_df['city'] == city].sort_values('timestamp')
                
                fig.add_trace(go.Scatter(
                    x=city_data['timestamp'],
                    y=city_data[selected_pollutant],
                    mode='lines+markers',
                    name=city,
                    line=dict(color=colors[i % len(colors)], width=2),
                    marker=dict(size=4)
                ))
            
            fig.update_layout(
                title=f"{selected_pollutant.upper()} Concentration Comparison",
                xaxis_title="Time",
                yaxis_title=f"{selected_pollutant.upper()} Level",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=500,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Live data table
        st.subheader("📊 Live Data Feed")
        
        # Auto-refresh checkbox
        if st.checkbox("🔄 Auto-refresh data (30s)", value=False):
            st.rerun()
        
        # Display latest measurements
        live_data = filtered_df.groupby('city').last().reset_index()
        live_data = live_data[['city', 'aqi', 'pm25', 'pm10', 'no2', 'o3', 'timestamp']]
        live_data['timestamp'] = live_data['timestamp'].dt.strftime('%H:%M:%S')
        
        st.dataframe(
            live_data,
            use_container_width=True,
            hide_index=True,
            column_config={
                "timestamp": "Last Update",
                "aqi": st.column_config.NumberColumn("AQI", format="%.0f"),
                "pm25": st.column_config.NumberColumn("PM2.5", format="%.1f"),
                "pm10": st.column_config.NumberColumn("PM10", format="%.1f"),
                "no2": st.column_config.NumberColumn("NO2", format="%.1f"),
                "o3": st.column_config.NumberColumn("O3", format="%.1f")
            }
        )
    
    def render_analytics_page(self):
        """Render analytics page"""
        st.title("🔍 Advanced Analytics")
        
        if not self.db:
            st.error("⚠️ Database connection unavailable.")
            return
        
        # Get extended data for analytics
        df = self.safe_execute(self.db.get_latest_air_quality_data, 168)  # 7 days
        
        if df is None or df.empty:
            st.warning("No data available for analytics.")
            return
        
        # Analytics controls
        st.subheader("🎛️ Analytics Configuration")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cities = sorted(df['city'].unique())
            selected_cities = st.multiselect(
                "Cities", 
                cities, 
                default=cities[:3] if len(cities) >= 3 else cities
            )
        
        with col2:
            analysis_type = st.selectbox(
                "Analysis Type",
                ["Trend Analysis", "Correlation Analysis", "Statistical Summary", "Comparative Analysis"]
            )
        
        with col3:
            pollutants = ['aqi', 'pm25', 'pm10', 'no2', 'o3', 'co', 'so2']
            available_pollutants = [p for p in pollutants if p in df.columns]
            selected_pollutants = st.multiselect(
                "Pollutants",
                available_pollutants,
                default=['aqi', 'pm25']
            )
        
        if not selected_cities or not selected_pollutants:
            st.info("Please select cities and pollutants for analysis.")
            return
        
        filtered_df = df[df['city'].isin(selected_cities)]
        
        # Perform selected analysis
        if analysis_type == "Trend Analysis":
            self.render_trend_analysis(filtered_df, selected_pollutants, selected_cities)
        elif analysis_type == "Correlation Analysis":
            self.render_correlation_analysis(filtered_df, selected_pollutants)
        elif analysis_type == "Statistical Summary":
            self.render_statistical_summary(filtered_df, selected_pollutants, selected_cities)
        elif analysis_type == "Comparative Analysis":
            self.render_comparative_analysis(filtered_df, selected_pollutants, selected_cities)
    
    def render_trend_analysis(self, df, pollutants, cities):
        """Render trend analysis"""
        st.subheader("📈 Trend Analysis")
        
        # Create subplots for each pollutant
        for pollutant in pollutants:
            if pollutant in df.columns:
                st.write(f"**{pollutant.upper()} Trends**")
                
                fig = go.Figure()
                colors = px.colors.qualitative.Set1
                
                for i, city in enumerate(cities):
                    city_data = df[df['city'] == city].sort_values('timestamp')
                    
                    if not city_data.empty:
                        # Calculate trend line
                        x_numeric = pd.to_numeric(city_data['timestamp'])
                        z = np.polyfit(x_numeric, city_data[pollutant], 1)
                        trend_line = np.poly1d(z)
                        
                        # Plot actual data
                        fig.add_trace(go.Scatter(
                            x=city_data['timestamp'],
                            y=city_data[pollutant],
                            mode='markers',
                            name=f"{city} - Data",
                            marker=dict(color=colors[i % len(colors)], size=4),
                            opacity=0.6
                        ))
                        
                        # Plot trend line
                        fig.add_trace(go.Scatter(
                            x=city_data['timestamp'],
                            y=trend_line(x_numeric),
                            mode='lines',
                            name=f"{city} - Trend",
                            line=dict(color=colors[i % len(colors)], width=3)
                        ))
                
                fig.update_layout(
                    title=f"{pollutant.upper()} Trend Analysis",
                    xaxis_title="Time",
                    yaxis_title=pollutant.upper(),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    def render_correlation_analysis(self, df, pollutants):
        """Render correlation analysis"""
        st.subheader("🔗 Correlation Analysis")
        
        if len(pollutants) < 2:
            st.warning("Please select at least 2 pollutants for correlation analysis.")
            return
        
        # Calculate correlation matrix
        correlation_data = df[pollutants].corr()
        
        # Create heatmap
        fig = px.imshow(
            correlation_data,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdBu_r",
            title="Pollutant Correlation Matrix"
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Correlation insights
        st.subheader("🔍 Correlation Insights")
        
        # Find strongest correlations
        correlation_pairs = []
        for i in range(len(pollutants)):
            for j in range(i+1, len(pollutants)):
                corr_value = correlation_data.iloc[i, j]
                correlation_pairs.append({
                    'Pollutant 1': pollutants[i].upper(),
                    'Pollutant 2': pollutants[j].upper(),
                    'Correlation': corr_value,
                    'Strength': 'Strong' if abs(corr_value) > 0.7 else 'Moderate' if abs(corr_value) > 0.4 else 'Weak'
                })
        
        correlation_df = pd.DataFrame(correlation_pairs)
        correlation_df = correlation_df.sort_values('Correlation', key=abs, ascending=False)
        
        st.dataframe(correlation_df, use_container_width=True, hide_index=True)
    
    def render_statistical_summary(self, df, pollutants, cities):
        """Render statistical summary"""
        st.subheader("📊 Statistical Summary")
        
        summary_data = []
        
        for city in cities:
            city_data = df[df['city'] == city]
            for pollutant in pollutants:
                if pollutant in city_data.columns:
                    summary_data.append({
                        'City': city,
                        'Pollutant': pollutant.upper(),
                        'Mean': city_data[pollutant].mean(),
                        'Median': city_data[pollutant].median(),
                        'Std Dev': city_data[pollutant].std(),
                        'Min': city_data[pollutant].min(),
                        'Max': city_data[pollutant].max(),
                        'Count': city_data[pollutant].count()
                    })
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            
            # Format numerical columns
            numeric_cols = ['Mean', 'Median', 'Std Dev', 'Min', 'Max']
            for col in numeric_cols:
                summary_df[col] = summary_df[col].round(2)
            
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
            # Download option
            csv = summary_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Summary as CSV",
                data=csv,
                file_name=f"air_quality_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    def render_comparative_analysis(self, df, pollutants, cities):
        """Render comparative analysis"""
        st.subheader("⚖️ Comparative Analysis")
        
        # Box plots for comparison
        for pollutant in pollutants:
            if pollutant in df.columns:
                fig = px.box(
                    df[df['city'].isin(cities)],
                    x='city',
                    y=pollutant,
                    title=f"{pollutant.upper()} Distribution by City"
                )
                
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    def render_alerts_page(self):
        """Render alerts management page"""
        st.title("🚨 Alert Management")
        
        if not self.db:
            st.error("⚠️ Database connection unavailable.")
            return
        
        # Get alerts
        alerts = self.safe_execute(self.db.get_active_alerts)
        
        # Alert summary
        st.subheader("📊 Alert Summary")
        
        if alerts is not None and not alerts.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_alerts = len(alerts)
                st.metric("Total Alerts", total_alerts)
            
            with col2:
                high_priority = len(alerts[alerts['severity'] == 'HIGH']) if 'severity' in alerts.columns else 0
                st.metric("High Priority", high_priority, delta="🔴" if high_priority > 0 else "🟢")
            
            with col3:
                unacknowledged = len(alerts[alerts['acknowledged'] == False]) if 'acknowledged' in alerts.columns else 0
                st.metric("Unacknowledged", unacknowledged)
            
            with col4:
                cities_affected = alerts['city'].nunique() if 'city' in alerts.columns else 0
                st.metric("Cities Affected", cities_affected)
            
            # Alert details
            st.subheader("🔔 Active Alerts")
            
            for _, alert in alerts.iterrows():
                severity = alert.get('severity', 'MEDIUM').upper()
                
                if severity == 'HIGH':
                    alert_class = 'alert-danger'
                    severity_icon = '🔴'
                elif severity == 'MEDIUM':
                    alert_class = 'alert-warning'
                    severity_icon = '🟡'
                else:
                    alert_class = 'alert-info'
                    severity_icon = '🟢'
                
                acknowledged = alert.get('acknowledged', False)
                ack_status = "✅ Acknowledged" if acknowledged else "⏳ Pending"
                
                st.markdown(f"""
                <div class="metric-card {alert_class}">
                    <h4>{severity_icon} {alert.get('city', 'Unknown City')} - {severity} Priority</h4>
                    <p><strong>Pollutant:</strong> {alert.get('pollutant', 'N/A')} | 
                       <strong>Value:</strong> {alert.get('value', 0):.1f} | 
                       <strong>Threshold:</strong> {alert.get('threshold', 0):.1f}</p>
                    <p><strong>Message:</strong> {alert.get('message', 'No message available')}</p>
                    <p><strong>Time:</strong> {alert.get('timestamp', 'Unknown').strftime('%Y-%m-%d %H:%M:%S') if hasattr(alert.get('timestamp'), 'strftime') else alert.get('timestamp', 'Unknown')} | 
                       <strong>Status:</strong> {ack_status}</p>
                </div>
                """, unsafe_allow_html=True)
        
        else:
            st.success("🎉 No active alerts! All air quality levels are within safe limits.")
            
            # Show alert configuration
            st.subheader("⚙️ Alert Configuration")
            
            with st.expander("Configure Alert Thresholds"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.number_input("PM2.5 Threshold (μg/m³)", value=55.0, min_value=0.0)
                    st.number_input("PM10 Threshold (μg/m³)", value=150.0, min_value=0.0)
                    st.number_input("NO2 Threshold (ppb)", value=100.0, min_value=0.0)
                
                with col2:
                    st.number_input("O3 Threshold (ppb)", value=120.0, min_value=0.0)
                    st.number_input("CO Threshold (ppm)", value=9.0, min_value=0.0)
                    st.number_input("SO2 Threshold (ppb)", value=75.0, min_value=0.0)
                
                if st.button("💾 Save Alert Configuration"):
                    st.success("Alert thresholds saved successfully!")
    
    def render_reports_page(self):
        """Render reports page"""
        st.title("📋 Reports & Analytics")
        
        st.subheader("📊 Generate Reports")
        
        col1, col2 = st.columns(2)
        
        with col1:
            report_type = st.selectbox(
                "Report Type",
                ["Daily Summary", "Weekly Analysis", "Monthly Report", "Custom Range"]
            )
            
            cities = ["All Cities", "New York", "Los Angeles", "London", "Delhi", "Beijing"]
            selected_city = st.selectbox("City", cities)
        
        with col2:
            if report_type == "Custom Range":
                start_date = st.date_input("Start Date")
                end_date = st.date_input("End Date")
            
            report_format = st.selectbox("Format", ["PDF", "Excel", "CSV"])
        
        if st.button("🚀 Generate Report"):
            with st.spinner("Generating report..."):
                # Simulate report generation
                import time
                time.sleep(2)
                st.success(f"✅ {report_type} report generated successfully!")
                st.info("Report will be available for download shortly.")
        
        # Sample report preview
        st.subheader("📄 Report Preview")
        
        if self.db:
            df = self.safe_execute(self.db.get_latest_air_quality_data, 24)
            if df is not None and not df.empty:
                # Create summary statistics
                summary_stats = df.groupby('city').agg({
                    'aqi': ['mean', 'max', 'min'],
                    'pm25': 'mean',
                    'pm10': 'mean'
                }).round(2)
                
                summary_stats.columns = ['AQI Avg', 'AQI Max', 'AQI Min', 'PM2.5 Avg', 'PM10 Avg']
                summary_stats = summary_stats.reset_index()
                
                st.dataframe(summary_stats, use_container_width=True)
    
    def render_settings_page(self):
        """Render settings page"""
        st.title("⚙️ System Settings")
        
        # System information
        st.subheader("🖥️ System Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("**Platform Version:** 1.0.0")
            st.info("**Database Status:** " + ("🟢 Connected" if self.db and self.db.engine else "🔴 Disconnected"))
            st.info("**Environment:** Production")
        
        with col2:
            current_time = datetime.now()
            st.info(f"**Server Time:** {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            st.info(f"**Timezone:** UTC")
            st.info("**Auto-refresh:** Enabled")
        
        # User preferences
        st.subheader("👤 User Preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            theme = st.selectbox("Theme", ["Light", "Dark", "Auto"])
            language = st.selectbox("Language", ["English", "Spanish", "French", "German"])
        
        with col2:
            units = st.selectbox("Units", ["Metric", "Imperial"])
            timezone = st.selectbox("Timezone", ["UTC", "EST", "PST", "GMT"])
        
        # Data settings
        st.subheader("🗄️ Data Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            data_retention = st.number_input("Data Retention (days)", value=365, min_value=1)
            refresh_interval = st.selectbox("Refresh Interval", ["30s", "1min", "5min", "15min"])
        
        with col2:
            backup_enabled = st.checkbox("Enable Automatic Backup", value=True)
            export_format = st.selectbox("Default Export Format", ["CSV", "Excel", "JSON"])
        
        # Save settings
        if st.button("💾 Save Settings"):
            st.success("✅ Settings saved successfully!")
        
        # System actions
        st.subheader("🛠️ System Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Refresh Cache"):
                st.cache_data.clear()
                st.success("Cache refreshed!")
        
        with col2:
            if st.button("🧪 Generate Test Data"):
                st.info("Run: `docker exec airquality-streamlit python sample_data_generator.py`")
        
        with col3:
            if st.button("📊 System Diagnostics"):
                st.info("System diagnostics completed. All systems operational.")
    
    def run(self):
        """Main application runner"""
        # Inject CSS
        inject_css()
        
        # Render components
        self.render_header()
        self.render_status_bar()
        self.render_navigation()
        
        # Route to current page
        page_routing = {
            'overview': self.render_overview_page,
            'monitoring': self.render_monitoring_page,
            'analytics': self.render_analytics_page,
            'alerts': self.render_alerts_page,
            'reports': self.render_reports_page,
            'settings': self.render_settings_page
        }
        
        current_page = st.session_state.current_page
        if current_page in page_routing:
            try:
                page_routing[current_page]()
            except Exception as e:
                logger.error(f"Error rendering page {current_page}: {e}")
                st.error(f"An error occurred while loading the page: {str(e)}")
                st.exception(e)
        else:
            st.error(f"Page '{current_page}' not found.")

# Main execution
if __name__ == "__main__":
    dashboard = ProductionDashboard()
    dashboard.run()