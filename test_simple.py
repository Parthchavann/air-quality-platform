import streamlit as st
import pandas as pd
import plotly.express as px

st.title("🌍 Air Quality Platform Test")
st.write("Testing basic Streamlit functionality")

# Simple data
data = {
    'City': ['New York', 'London', 'Tokyo', 'Delhi'],
    'AQI': [50, 45, 60, 120]
}
df = pd.DataFrame(data)

st.subheader("Sample Air Quality Data")
st.dataframe(df)

# Simple chart
fig = px.bar(df, x='City', y='AQI', title='Air Quality Index by City')
st.plotly_chart(fig)

st.success("✅ Streamlit is working correctly!")