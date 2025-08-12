#!/usr/bin/env python3

import streamlit as st
import requests
import time

st.title("🧪 Dashboard Test")

st.write("Testing if premium dashboard is accessible...")

try:
    response = requests.get("http://localhost:8502")
    st.write(f"Response status: {response.status_code}")
    
    if "AirFlow Analytics" in response.text:
        st.success("✅ Premium dashboard is running!")
    else:
        st.warning("⚠️ Basic dashboard might be running instead")
        
    st.write("Page title found:", response.text[response.text.find("<title>"):response.text.find("</title>")+8] if "<title>" in response.text else "No title found")
    
except Exception as e:
    st.error(f"Error: {e}")
    
st.write("---")
st.write("Current time:", time.strftime("%Y-%m-%d %H:%M:%S"))