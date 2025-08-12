import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="Air Quality Dashboard",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Air Quality Monitoring Platform")
st.markdown("### Live Air Quality Data Dashboard")

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

# Sidebar
st.sidebar.header("Filter Options")
selected_cities = st.sidebar.multiselect(
    "Select Cities",
    options=df['city'].unique(),
    default=df['city'].unique()
)

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(df['timestamp'].min(), df['timestamp'].max()),
    min_value=df['timestamp'].min(),
    max_value=df['timestamp'].max()
)

# Filter data
filtered_df = df[df['city'].isin(selected_cities)]
if len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df['timestamp'].dt.date >= date_range[0]) &
        (filtered_df['timestamp'].dt.date <= date_range[1])
    ]

# Metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    avg_aqi = filtered_df['aqi'].mean()
    st.metric("Average AQI", f"{avg_aqi:.1f}")

with col2:
    avg_pm25 = filtered_df['pm2.5'].mean()
    st.metric("Avg PM2.5", f"{avg_pm25:.1f} μg/m³")

with col3:
    max_aqi = filtered_df['aqi'].max()
    st.metric("Max AQI", f"{max_aqi}")

with col4:
    num_cities = filtered_df['city'].nunique()
    st.metric("Cities Monitored", num_cities)

# Charts
st.markdown("### Air Quality Trends")

# AQI over time
fig_aqi = px.line(
    filtered_df,
    x='timestamp',
    y='aqi',
    color='city',
    title='AQI Over Time',
    labels={'aqi': 'Air Quality Index', 'timestamp': 'Date'}
)
st.plotly_chart(fig_aqi, use_container_width=True)

# PM2.5 distribution
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

# Data table
st.markdown("### Recent Measurements")
st.dataframe(
    filtered_df.sort_values('timestamp', ascending=False).head(20),
    use_container_width=True
)

# Footer
st.markdown("---")
st.markdown("🔄 Dashboard refreshes every 5 seconds | 📊 Showing sample data for demonstration")