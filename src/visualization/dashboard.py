import streamlit as st
import psycopg2
import pandas as pd

st.title("🌍 Air Quality Dashboard")

try:
    conn = psycopg2.connect(
        host='postgres',
        port=5432,
        database='airquality',
        user='airquality_user',
        password='secure_password'
    )
    
    query = "SELECT * FROM air_quality_measurements ORDER BY city"
    df = pd.read_sql_query(query, conn)
    
    st.write(f"Debug: Query returned {len(df)} rows")
    st.write(f"Debug: DataFrame empty: {df.empty}")
    
    if not df.empty:
        st.success(f"✅ Found {len(df)} measurements")
        
        # Show the actual data
        st.subheader("Raw Data")
        st.dataframe(df)
        
        # Show specific columns
        display_df = df[['city', 'country', 'aqi', 'pm25', 'timestamp']].copy()
        st.subheader("Air Quality Summary")
        st.dataframe(display_df)
        
        # Metrics
        st.subheader("Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Cities", len(df['city'].unique()))
        with col2:
            st.metric("Avg AQI", f"{df['aqi'].mean():.0f}")
        with col3:
            st.metric("Max AQI", df['aqi'].max())
            
    else:
        st.error("❌ DataFrame is empty!")
        
        # Debug: show what's in the table
        debug_query = "SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM air_quality_measurements"
        debug_df = pd.read_sql_query(debug_query, conn)
        st.write("Debug info:", debug_df)
        
    conn.close()
    
except Exception as e:
    st.error(f"Error: {e}")
    import traceback
    st.text(traceback.format_exc())