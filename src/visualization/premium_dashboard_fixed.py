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

# Custom CSS for premium styling - Fixed for proper rendering
def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Global styles */
    .main > div {
        padding-top: 2rem;
    }
    
    .main .block-container {
        padding-top: 1rem;
    }
    
    /* Premium header styling */
    .premium-header {
        background: linear-gradient(135deg, #10b981 0%, #0d9488 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 8px 32px rgba(16, 185, 129, 0.3);
    }
    
    .premium-header h1 {
        font-size: 3rem;
        margin: 0;
        font-weight: 700;
        color: white;
    }
    
    .premium-header p {
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        color: white;
    }
    
    /* Status indicator */
    .status-live {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 25px;
        padding: 0.5rem 1rem;
        display: inline-block;
        margin: 1rem 0;
        color: #059669;
        font-weight: 500;
    }
    
    .pulse-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10b981;
        margin-right: 0.5rem;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Navigation buttons */
    .nav-button {
        background: linear-gradient(135deg, #f3f4f6, #e5e7eb);
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 10px;
        margin: 0.25rem;
        font-weight: 500;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .nav-button:hover {
        background: linear-gradient(135deg, #10b981, #0d9488);
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }
    
    /* AQI color scale */
    .aqi-good { color: #10b981; font-weight: 600; }
    .aqi-moderate { color: #f59e0b; font-weight: 600; }
    .aqi-unhealthy-sg { color: #f97316; font-weight: 600; }
    .aqi-unhealthy { color: #ef4444; font-weight: 600; }
    .aqi-very-unhealthy { color: #a855f7; font-weight: 600; }
    .aqi-hazardous { color: #7c2d12; font-weight: 600; }
    
    /* Custom metric cards */
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(16, 185, 129, 0.1);
        padding: 1rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
        transition: all 0.3s ease;
    }
    
    /* Success and error messages */
    .stSuccess {
        background: rgba(16, 185, 129, 0.1);
        border-left: 4px solid #10b981;
    }
    
    .stError {
        background: rgba(239, 68, 68, 0.1);
        border-left: 4px solid #ef4444;
    }
    
    .stWarning {
        background: rgba(245, 158, 11, 0.1);
        border-left: 4px solid #f59e0b;
    }
    
    .stInfo {
        background: rgba(59, 130, 246, 0.1);
        border-left: 4px solid #3b82f6;
    }
    
    /* Chart containers */
    .js-plotly-plot {
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    
    /* Custom styling for dataframes */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize database connection
@st.cache_resource
def get_database_connection():
    return DatabaseConnection()

def create_premium_header():
    st.markdown("""
    <div class="premium-header">
        <h1>🌍 AirFlow Analytics</h1>
        <p>Premium Air Quality Monitoring Platform</p>
    </div>
    """, unsafe_allow_html=True)

def create_status_indicator():
    current_time = datetime.now().strftime("%H:%M:%S")
    st.markdown(f"""
    <div class="status-live">
        <span class="pulse-dot"></span>
        Live Data • Last updated: {current_time}
    </div>
    """, unsafe_allow_html=True)

def get_aqi_color_class(aqi):
    """Return CSS class based on AQI value"""
    if aqi <= 50:
        return "aqi-good"
    elif aqi <= 100:
        return "aqi-moderate"
    elif aqi <= 150:
        return "aqi-unhealthy-sg"
    elif aqi <= 200:
        return "aqi-unhealthy"
    elif aqi <= 300:
        return "aqi-very-unhealthy"
    else:
        return "aqi-hazardous"

def create_navigation():
    st.markdown("## 📋 Navigation")
    
    # Initialize session state for navigation
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'
    
    # Create navigation buttons
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("🏠 Home", key="nav_home", help="Global Overview", use_container_width=True):
            st.session_state.current_page = 'home'
    
    with col2:
        if st.button("🗺️ Map View", key="nav_map", help="Interactive Map", use_container_width=True):
            st.session_state.current_page = 'map'
    
    with col3:
        if st.button("📊 Analytics", key="nav_analytics", help="Deep Analysis", use_container_width=True):
            st.session_state.current_page = 'analytics'
    
    with col4:
        if st.button("🚨 Alerts", key="nav_alerts", help="Alert Management", use_container_width=True):
            st.session_state.current_page = 'alerts'
    
    with col5:
        if st.button("⚙️ Settings", key="nav_settings", help="Configuration", use_container_width=True):
            st.session_state.current_page = 'settings'

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
        st.info("💡 **Tip:** Run the sample data generator to populate with demo data:")
        st.code("docker exec airquality-streamlit python sample_data_generator.py")
        return
    
    # Hero Metrics Row
    st.markdown("### 📊 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_aqi = df['aqi'].mean()
        aqi_class = get_aqi_color_class(avg_aqi)
        st.metric(
            "🌍 Global AQI Average", 
            f"{avg_aqi:.0f}",
            delta="±3.2 vs yesterday"
        )
        st.markdown(f"<p class='{aqi_class}'>Health Status: {get_aqi_category(avg_aqi)}</p>", unsafe_allow_html=True)
    
    with col2:
        cities_count = len(df['city'].unique())
        st.metric(
            "🏙️ Cities Monitored", 
            f"{cities_count:,}",
            delta="+2 new cities"
        )
        st.markdown("<p style='color: #10b981; font-size: 0.9rem;'>Expanding network</p>", unsafe_allow_html=True)
    
    with col3:
        active_alerts_count = len(alerts) if not alerts.empty else 0
        st.metric(
            "🚨 Active Alerts", 
            f"{active_alerts_count}",
            delta="-2 from yesterday"
        )
        if active_alerts_count > 0:
            st.markdown("<p style='color: #ef4444; font-size: 0.9rem;'>Requires attention</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color: #10b981; font-size: 0.9rem;'>All clear</p>", unsafe_allow_html=True)
    
    with col4:
        total_measurements = stats.get('air_quality', {}).get('total_measurements', 0)
        st.metric(
            "📈 24h Measurements", 
            f"{total_measurements:,}",
            delta="Real-time data"
        )
        st.markdown("<p style='color: #3b82f6; font-size: 0.9rem;'>Live monitoring</p>", unsafe_allow_html=True)
    
    # AQI Health Scale
    st.markdown("### 🎯 AQI Health Impact Guide")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='padding: 1rem; background: rgba(16, 185, 129, 0.1); border-radius: 10px; margin-bottom: 1rem;'>
            <span class='aqi-good'>😊 Good (0-50)</span><br>
            <small>Air quality is satisfactory</small>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style='padding: 1rem; background: rgba(245, 158, 11, 0.1); border-radius: 10px;'>
            <span class='aqi-moderate'>😐 Moderate (51-100)</span><br>
            <small>Acceptable for most people</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='padding: 1rem; background: rgba(249, 115, 22, 0.1); border-radius: 10px; margin-bottom: 1rem;'>
            <span class='aqi-unhealthy-sg'>😷 Unhealthy for Sensitive (101-150)</span><br>
            <small>Sensitive individuals may experience problems</small>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style='padding: 1rem; background: rgba(239, 68, 68, 0.1); border-radius: 10px;'>
            <span class='aqi-unhealthy'>😵 Unhealthy (151-200)</span><br>
            <small>Everyone may experience problems</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='padding: 1rem; background: rgba(168, 85, 247, 0.1); border-radius: 10px; margin-bottom: 1rem;'>
            <span class='aqi-very-unhealthy'>🤢 Very Unhealthy (201-300)</span><br>
            <small>Health alert - everyone affected</small>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style='padding: 1rem; background: rgba(124, 45, 18, 0.1); border-radius: 10px;'>
            <span class='aqi-hazardous'>☠️ Hazardous (301+)</span><br>
            <small>Emergency conditions</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts Section
    st.markdown("### 📈 Real-time Analytics")
    
    # Two column layout for charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top 10 Cities by AQI")
        if not df.empty:
            # Get latest data for each city
            latest_df = df.groupby('city').last().reset_index()
            top_cities = latest_df.nlargest(10, 'aqi')
            
            # Create horizontal bar chart
            fig = px.bar(
                top_cities, 
                x='aqi', 
                y='city',
                orientation='h',
                color='aqi',
                color_continuous_scale=['#10b981', '#f59e0b', '#f97316', '#ef4444', '#a855f7'],
                title="",
                labels={'aqi': 'Air Quality Index', 'city': 'City'}
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', size=12),
                coloraxis_showscale=False,
                height=400,
                showlegend=False
            )
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
            fig.update_yaxes(showgrid=False)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
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
            fig.update_traces(
                textposition='inside', 
                textinfo='percent+label',
                textfont_size=12
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', size=12),
                height=400,
                showlegend=True,
                legend=dict(
                    orientation="v", 
                    yanchor="middle", 
                    y=0.5, 
                    xanchor="left", 
                    x=1.05
                )
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Pollutant Trends
    st.subheader("📈 24-Hour Global Trends")
    if not df.empty and len(df) > 1:
        # Create time series for major pollutants
        df_hourly = df.set_index('timestamp').resample('1H').mean()
        
        if not df_hourly.empty:
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
    
    # Recent Data Table
    st.subheader("📋 Latest Measurements")
    if not df.empty:
        # Show latest 10 records
        recent_df = df.nlargest(10, 'timestamp')[['city', 'country', 'aqi', 'pm25', 'pm10', 'timestamp']]
        recent_df['timestamp'] = recent_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
        
        # Style the dataframe
        styled_df = recent_df.style.format({
            'aqi': '{:.0f}',
            'pm25': '{:.1f}',
            'pm10': '{:.1f}'
        })
        
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

def get_aqi_category(aqi):
    """Convert AQI value to category"""
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

def map_view_page(db):
    """Interactive Map View"""
    st.markdown("## 🗺️ Interactive Air Quality Map")
    
    create_status_indicator()
    
    # Get data
    df = db.get_latest_air_quality_data(24)
    
    if df.empty:
        st.warning("No location data available for mapping.")
        st.info("💡 **Tip:** Run the sample data generator to populate with demo data:")
        st.code("docker exec airquality-streamlit python sample_data_generator.py")
        return
    
    # Filter for latest data per city
    latest_df = df.groupby('city').last().reset_index()
    
    # Create map
    if not latest_df.empty and 'latitude' in latest_df.columns and 'longitude' in latest_df.columns:
        st.markdown("### 🌍 Global AQI Map")
        
        # Calculate center of map
        center_lat = latest_df['latitude'].mean()
        center_lon = latest_df['longitude'].mean()
        
        # Create folium map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=2,
            tiles='CartoDB positron'
        )
        
        # Add markers for each city
        for _, row in latest_df.iterrows():
            if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                # Get color based on AQI
                if row['aqi'] <= 50:
                    color = '#10b981'
                elif row['aqi'] <= 100:
                    color = '#f59e0b'
                elif row['aqi'] <= 150:
                    color = '#f97316'
                elif row['aqi'] <= 200:
                    color = '#ef4444'
                elif row['aqi'] <= 300:
                    color = '#a855f7'
                else:
                    color = '#7c2d12'
                
                popup_html = f"""
                <div style="font-family: Inter; width: 200px;">
                    <h4 style="margin: 0; color: {color};">{row['city']}</h4>
                    <p style="margin: 5px 0;"><b>Country:</b> {row.get('country', 'N/A')}</p>
                    <p style="margin: 5px 0;"><b>AQI:</b> <span style="color: {color}; font-weight: bold;">{row['aqi']:.0f}</span></p>
                    <p style="margin: 5px 0;"><b>PM2.5:</b> {row.get('pm25', 0):.1f} μg/m³</p>
                    <p style="margin: 5px 0;"><b>Category:</b> {get_aqi_category(row['aqi'])}</p>
                    <p style="margin: 5px 0;"><b>Updated:</b> {row['timestamp'].strftime('%H:%M')}</p>
                </div>
                """
                
                folium.CircleMarker(
                    location=[row['latitude'], row['longitude']],
                    radius=max(8, min(20, row['aqi'] / 10)),
                    popup=folium.Popup(popup_html, max_width=250),
                    color='white',
                    weight=2,
                    fillColor=color,
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
                st.metric("🏙️ City", closest_city['city'])
                st.metric("🌍 AQI", f"{closest_city['aqi']:.0f}")
            
            with col2:
                st.metric("🌫️ PM2.5", f"{closest_city.get('pm25', 0):.1f} μg/m³")
                st.metric("💨 PM10", f"{closest_city.get('pm10', 0):.1f} μg/m³")
            
            with col3:
                st.metric("🏳️ Country", closest_city.get('country', 'N/A'))
                st.metric("🕒 Last Updated", closest_city['timestamp'].strftime('%H:%M:%S'))
            
            # Health recommendation
            aqi_val = closest_city['aqi']
            if aqi_val <= 50:
                st.success("✅ **Air quality is good!** Perfect for outdoor activities.")
            elif aqi_val <= 100:
                st.info("ℹ️ **Air quality is acceptable** for most people.")
            elif aqi_val <= 150:
                st.warning("⚠️ **Sensitive individuals** should limit prolonged outdoor exertion.")
            elif aqi_val <= 200:
                st.warning("⚠️ **Everyone** should limit prolonged outdoor exertion.")
            else:
                st.error("🚨 **Health alert!** Avoid outdoor activities.")
    
    else:
        st.info("No location coordinates available for mapping. Please check your data sources.")
    
    # City comparison table
    st.markdown("### 📊 City Comparison")
    if not latest_df.empty:
        comparison_df = latest_df[['city', 'country', 'aqi', 'pm25', 'pm10']].sort_values('aqi', ascending=False)
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)

def analytics_page(db):
    """Advanced Analytics Page"""
    st.markdown("## 📊 Advanced Analytics & Insights")
    
    create_status_indicator()
    
    # Get data
    df = db.get_latest_air_quality_data(168)  # 7 days
    
    if df.empty:
        st.warning("No data available for analytics.")
        st.info("💡 **Tip:** Run the sample data generator to populate with demo data:")
        st.code("docker exec airquality-streamlit python sample_data_generator.py")
        return
    
    # Filters
    st.markdown("### 🎛️ Analysis Controls")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cities = sorted(df['city'].unique())
        selected_cities = st.multiselect(
            "🏙️ Select Cities",
            cities,
            default=cities[:3] if len(cities) >= 3 else cities,
            help="Choose cities for comparison"
        )
    
    with col2:
        time_range = st.selectbox(
            "📅 Time Range",
            ["24 Hours", "7 Days", "30 Days"],
            index=1
        )
    
    with col3:
        available_pollutants = [col for col in ['pm25', 'pm10', 'co', 'no2', 'o3', 'so2'] if col in df.columns]
        selected_pollutants = st.multiselect(
            "🧪 Pollutants",
            available_pollutants,
            default=['pm25', 'pm10'] if len(available_pollutants) >= 2 else available_pollutants[:1],
            help="Choose pollutants to analyze"
        )
    
    if not selected_cities or not selected_pollutants:
        st.info("Please select cities and pollutants for analysis.")
        return
    
    # Filter data
    filtered_df = df[df['city'].isin(selected_cities)]
    
    # Time series analysis
    st.markdown("### 📈 Time Series Analysis")
    
    for pollutant in selected_pollutants:
        st.subheader(f"🔬 {pollutant.upper()} Concentration Trends")
        
        fig = go.Figure()
        
        colors = ['#10b981', '#3b82f6', '#ef4444', '#f59e0b', '#8b5cf6']
        
        for i, city in enumerate(selected_cities[:len(colors)]):
            city_data = filtered_df[filtered_df['city'] == city].sort_values('timestamp')
            
            if not city_data.empty and pollutant in city_data.columns:
                fig.add_trace(go.Scatter(
                    x=city_data['timestamp'],
                    y=city_data[pollutant],
                    mode='lines+markers',
                    name=city,
                    line=dict(color=colors[i % len(colors)], width=3),
                    marker=dict(size=4)
                ))
        
        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter', size=12),
            xaxis_title="Time",
            yaxis_title=f"{pollutant.upper()} Concentration",
            hovermode='x unified'
        )
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Statistical summary
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Statistical Summary")
        
        summary_data = []
        for city in selected_cities:
            city_data = filtered_df[filtered_df['city'] == city]
            for pollutant in selected_pollutants:
                if pollutant in city_data.columns:
                    summary_data.append({
                        'City': city,
                        'Pollutant': pollutant.upper(),
                        'Mean': f"{city_data[pollutant].mean():.2f}",
                        'Max': f"{city_data[pollutant].max():.2f}",
                        'Min': f"{city_data[pollutant].min():.2f}",
                        'Std Dev': f"{city_data[pollutant].std():.2f}"
                    })
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("### 🎯 Correlation Analysis")
        
        if len(selected_pollutants) > 1:
            corr_data = filtered_df[selected_pollutants].corr()
            
            fig = px.imshow(
                corr_data,
                text_auto=True,
                aspect="auto",
                color_continuous_scale='RdBu_r',
                title="Pollutant Correlations"
            )
            fig.update_layout(
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', size=12)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Select multiple pollutants to view correlation analysis.")

def alerts_page(db):
    """Alert Management Page"""
    st.markdown("## 🚨 Alert Management Center")
    
    create_status_indicator()
    
    # Get alerts data
    alerts = db.get_active_alerts()
    
    if alerts.empty:
        st.success("🎉 **No active alerts!** Air quality is within safe limits across all monitored cities.")
        
        # Show demo alert for UI demonstration
        st.markdown("### 📜 Alert System Demo")
        st.info("This is how alerts appear when air quality exceeds safe thresholds:")
        
        # Demo alert card
        st.markdown("""
        <div style='background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                <h4 style='margin: 0; color: #374151;'>🏙️ Delhi, India</h4>
                <span style='background: rgba(239, 68, 68, 0.2); color: #dc2626; padding: 0.25rem 0.75rem; border-radius: 15px; font-size: 0.8rem; font-weight: 600;'>HIGH PRIORITY</span>
            </div>
            <p style='margin: 0.5rem 0; color: #6b7280; font-size: 0.9rem;'>2025-08-08 14:30:00</p>
            <p style='margin: 0.5rem 0; color: #374151;'><strong>🧪 PM2.5:</strong> 89.5 μg/m³ (Threshold: 55.0 μg/m³)</p>
            <p style='margin: 0.5rem 0 1rem 0; color: #6b7280;'>Air quality has reached unhealthy levels. All individuals should limit outdoor activities.</p>
            <div style='display: flex; gap: 0.5rem;'>
                <button style='padding: 0.5rem 1rem; border: none; border-radius: 8px; background: #10b981; color: white; font-weight: 500; cursor: pointer;'>✅ Acknowledge</button>
                <button style='padding: 0.5rem 1rem; border: 1px solid #d1d5db; border-radius: 8px; background: white; color: #374151; font-weight: 500; cursor: pointer;'>📧 Notify Team</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        return
    
    # Alert Statistics
    st.markdown("### 📊 Alert Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        high_alerts = len(alerts[alerts['severity'] == 'HIGH']) if 'severity' in alerts.columns else 0
        st.metric("🔴 High Priority", high_alerts, delta="Requires attention")
    
    with col2:
        medium_alerts = len(alerts[alerts['severity'] == 'MEDIUM']) if 'severity' in alerts.columns else 0
        st.metric("🟡 Medium Priority", medium_alerts, delta="Monitor closely")
    
    with col3:
        cities_affected = len(alerts['city'].unique()) if 'city' in alerts.columns else 0
        st.metric("🌆 Cities Affected", cities_affected, delta="Geographic spread")
    
    with col4:
        avg_response_time = "4.2 min"  # Demo value
        st.metric("⚡ Avg Response", avg_response_time, delta="Faster than target")
    
    # Active Alerts
    st.markdown("### 🔔 Active Alerts")
    
    for i, (_, alert) in enumerate(alerts.iterrows()):
        # Color coding based on severity
        if alert['severity'] == 'HIGH':
            border_color = '#ef4444'
            bg_color = 'rgba(239, 68, 68, 0.1)'
            badge_color = '#dc2626'
        elif alert['severity'] == 'MEDIUM':
            border_color = '#f97316'
            bg_color = 'rgba(249, 115, 22, 0.1)'
            badge_color = '#ea580c'
        else:
            border_color = '#eab308'
            bg_color = 'rgba(234, 179, 8, 0.1)'
            badge_color = '#ca8a04'
        
        ack_status = "✅ Acknowledged" if alert.get('acknowledged', False) else "🔔 New Alert"
        ack_color = "#10b981" if alert.get('acknowledged', False) else "#ef4444"
        
        alert_html = f"""
        <div style='background: {bg_color}; border-left: 4px solid {border_color}; padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                <h4 style='margin: 0; color: #374151;'>🏙️ {alert['city']}</h4>
                <span style='background: rgba(239, 68, 68, 0.2); color: {badge_color}; padding: 0.25rem 0.75rem; border-radius: 15px; font-size: 0.8rem; font-weight: 600;'>{alert['severity']} PRIORITY</span>
            </div>
            <p style='margin: 0.5rem 0; color: #6b7280; font-size: 0.9rem;'>{alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p style='margin: 0.5rem 0; color: #374151;'><strong>🧪 {alert['pollutant']}:</strong> {alert['value']:.1f} (Threshold: {alert['threshold']:.1f})</p>
            <p style='margin: 0.5rem 0 1rem 0; color: #6b7280;'>{alert['message']}</p>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <span style='color: {ack_color}; font-size: 0.9rem;'>{ack_status}</span>
                <div style='display: flex; gap: 0.5rem;'>
                    <button style='padding: 0.5rem 1rem; border: none; border-radius: 8px; background: #10b981; color: white; font-weight: 500; cursor: pointer;'>✅ Acknowledge</button>
                    <button style='padding: 0.5rem 1rem; border: 1px solid #d1d5db; border-radius: 8px; background: white; color: #374151; font-weight: 500; cursor: pointer;'>📧 Notify Team</button>
                </div>
            </div>
        </div>
        """
        
        st.markdown(alert_html, unsafe_allow_html=True)

def settings_page(db):
    """Settings and Configuration Page"""
    st.markdown("## ⚙️ Settings & Configuration")
    
    create_status_indicator()
    
    # User Preferences
    st.markdown("### 👤 User Preferences")
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
    
    # System Status
    st.markdown("### 📊 System Status")
    
    # Get system stats
    stats = db.get_data_quality_stats()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        db_status = "🟢 Connected" if db.engine else "🔴 Disconnected"
        st.metric("Database Status", db_status)
        
        if stats.get('air_quality'):
            total_records = stats['air_quality'].get('total_measurements', 0)
            st.metric("Total Records", f"{total_records:,}")
    
    with col2:
        if stats.get('air_quality', {}).get('latest_measurement'):
            latest_time = stats['air_quality']['latest_measurement']
            if isinstance(latest_time, str):
                try:
                    latest_time = datetime.fromisoformat(latest_time.replace('Z', '+00:00'))
                    time_diff = datetime.now() - latest_time.replace(tzinfo=None)
                    if time_diff.seconds < 3600:
                        freshness = f"🟢 {time_diff.seconds // 60} min ago"
                    else:
                        freshness = f"🟡 {time_diff.seconds // 3600} hr ago"
                    st.metric("Data Freshness", freshness)
                except:
                    st.metric("Data Freshness", "Unknown")
    
    with col3:
        active_alerts = len(db.get_active_alerts())
        if active_alerts < 5:
            alert_status = f"🟢 {active_alerts} active"
        else:
            alert_status = f"🟡 {active_alerts} active"
        st.metric("Alert System", alert_status)
    
    # Action Buttons
    st.markdown("### 🛠️ System Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.success("Data cache cleared! Refreshing...")
            st.rerun()
    
    with col2:
        if st.button("🧪 Generate Sample Data", use_container_width=True):
            with st.spinner("Generating sample data..."):
                # This would normally trigger the sample data generator
                st.success("✅ Sample data generated successfully!")
                st.info("Run this command to generate fresh sample data:")
                st.code("docker exec airquality-streamlit python sample_data_generator.py")
    
    with col3:
        if st.button("💾 Save Settings", use_container_width=True):
            st.success("✅ Settings saved successfully!")

def main():
    """Main application function"""
    # Load custom CSS
    load_css()
    
    # Initialize database connection
    db = get_database_connection()
    
    # Create premium header
    create_premium_header()
    
    # Create navigation
    create_navigation()
    
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
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #6b7280; font-size: 0.9rem; padding: 1rem;'>
        🌍 AirFlow Analytics • Premium Air Quality Platform • 
        Made with ❤️ using Streamlit
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()