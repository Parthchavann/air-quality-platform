"""
🌟 AirFlow Analytics - Lovable Premium Dashboard
Breathtakingly Beautiful Air Quality Monitoring Platform
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
    page_title="🌍 AirFlow Analytics",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Lovable CSS with Breathtaking Design
def inject_lovable_css():
    st.markdown("""
    <style>
    /* Import Premium Typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');
    
    /* CSS Variables for Design System */
    :root {
        /* Primary Colors */
        --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --primary-blue: #667eea;
        --primary-purple: #764ba2;
        
        /* Accent Colors */
        --emerald: #10b981;
        --sky-blue: #0ea5e9;
        --warm-amber: #f59e0b;
        
        /* Status Colors */
        --success: #22c55e;
        --warning: #eab308;
        --error: #ef4444;
        
        /* Neutrals */
        --white: #ffffff;
        --soft-gray: #f8fafc;
        --deep-charcoal: #1e293b;
        
        /* Spacing Scale */
        --space-xs: 0.5rem;
        --space-sm: 0.75rem;
        --space-md: 1rem;
        --space-lg: 1.5rem;
        --space-xl: 2rem;
        --space-2xl: 3rem;
        
        /* Typography Scale */
        --text-hero: 3.5rem;
        --text-header: 1.8rem;
        --text-body: 1rem;
        --text-small: 0.875rem;
        
        /* Animation Timing */
        --ease-smooth: cubic-bezier(0.4, 0, 0.2, 1);
        --duration-fast: 0.15s;
        --duration-normal: 0.3s;
        --duration-slow: 0.6s;
    }
    
    /* Breathtaking App Background */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: var(--primary-gradient);
        background-attachment: fixed;
        background-size: 400% 400%;
        animation: gradientFlow 15s ease infinite;
    }
    
    @keyframes gradientFlow {
        0%, 100% { background-position: 0% 50%; }
        25% { background-position: 100% 50%; }
        50% { background-position: 100% 100%; }
        75% { background-position: 0% 100%; }
    }
    
    /* Premium Glassmorphism Container */
    .main .block-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: var(--space-xl);
        margin-top: var(--space-md);
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        animation: containerEntrance 1s var(--ease-smooth) both;
    }
    
    @keyframes containerEntrance {
        from {
            opacity: 0;
            transform: translateY(20px) scale(0.98);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }
    
    /* Hide Streamlit Elements */
    #MainMenu, footer, .stDeployButton { visibility: hidden; }
    
    /* Breathtaking Metric Cards */
    div[data-testid="metric-container"] {
        background: linear-gradient(145deg, 
            rgba(255,255,255,0.95) 0%,
            rgba(255,255,255,0.8) 100%);
        border: 2px solid rgba(255,255,255,0.2);
        border-radius: 20px;
        padding: var(--space-lg);
        box-shadow: 
            0 8px 32px rgba(0,0,0,0.1),
            inset 0 1px 0 rgba(255,255,255,0.2);
        backdrop-filter: blur(10px);
        transition: all var(--duration-normal) var(--ease-smooth);
        position: relative;
        overflow: hidden;
        cursor: pointer;
        animation: cardEntrance 0.6s var(--ease-smooth) both;
    }
    
    @keyframes cardEntrance {
        from {
            opacity: 0;
            transform: translateY(30px) scale(0.95);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }
    
    /* Magical Hover Effects */
    div[data-testid="metric-container"]:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 
            0 20px 60px rgba(0,0,0,0.15),
            0 0 0 1px rgba(102, 126, 234, 0.3),
            inset 0 1px 0 rgba(255,255,255,0.4);
        background: linear-gradient(145deg, 
            rgba(255,255,255,1) 0%,
            rgba(255,255,255,0.95) 100%);
    }
    
    /* Shimmer Effect */
    div[data-testid="metric-container"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent 0%, 
            rgba(102, 126, 234, 0.1) 50%, 
            transparent 100%);
        transition: left var(--duration-slow);
    }
    
    div[data-testid="metric-container"]:hover::before {
        left: 100%;
    }
    
    /* Stunning Typography */
    h1 {
        background: var(--primary-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 900 !important;
        font-size: var(--text-hero) !important;
        text-align: center;
        margin-bottom: 0 !important;
        letter-spacing: -0.02em;
        animation: titleGlow 3s ease-in-out infinite alternate;
    }
    
    @keyframes titleGlow {
        from { filter: drop-shadow(0 0 20px rgba(102, 126, 234, 0.3)); }
        to { filter: drop-shadow(0 0 40px rgba(118, 75, 162, 0.5)); }
    }
    
    h2 {
        color: var(--deep-charcoal) !important;
        font-weight: 700 !important;
        font-size: var(--text-header) !important;
        margin-bottom: var(--space-md) !important;
        position: relative;
        padding-left: var(--space-md);
        animation: headerSlide 0.8s var(--ease-smooth) both;
    }
    
    @keyframes headerSlide {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    h2::before {
        content: '';
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 4px;
        height: 100%;
        background: var(--primary-gradient);
        border-radius: 2px;
        box-shadow: 0 0 10px rgba(102, 126, 234, 0.4);
    }
    
    h3 {
        color: rgba(30, 41, 59, 0.8) !important;
        font-weight: 600 !important;
        font-size: 1.4rem !important;
    }
    
    /* Premium Button Design */
    .stButton > button {
        background: var(--primary-gradient) !important;
        color: white !important;
        border: none !important;
        border-radius: 16px !important;
        padding: var(--space-sm) var(--space-xl) !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        transition: all var(--duration-normal) var(--ease-smooth) !important;
        box-shadow: 
            0 4px 15px rgba(102, 126, 234, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
        position: relative !important;
        overflow: hidden !important;
        cursor: pointer !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 
            0 8px 25px rgba(102, 126, 234, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
        background: linear-gradient(135deg, #5a6fd8 0%, #6b4499 100%) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0px) !important;
        animation: buttonPulse 0.2s var(--ease-smooth);
    }
    
    @keyframes buttonPulse {
        0% { transform: scale(1); }
        50% { transform: scale(0.98); }
        100% { transform: scale(1); }
    }
    
    /* Magical Sidebar */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.2) !important;
        animation: sidebarSlide 0.8s var(--ease-smooth) both;
    }
    
    @keyframes sidebarSlide {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    /* Navigation Button Magic */
    .css-1d391kg .stButton > button {
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 12px !important;
        margin-bottom: var(--space-sm) !important;
        transition: all var(--duration-normal) var(--ease-smooth) !important;
    }
    
    .css-1d391kg .stButton > button:hover {
        background: rgba(255, 255, 255, 0.2) !important;
        transform: translateX(5px) !important;
        box-shadow: 
            0 4px 20px rgba(255, 255, 255, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
    }
    
    /* Data Tables with Love */
    .stDataFrame {
        background: rgba(255, 255, 255, 0.95) !important;
        border-radius: 16px !important;
        overflow: hidden !important;
        box-shadow: 
            0 4px 20px rgba(0,0,0,0.08),
            inset 0 1px 0 rgba(255,255,255,0.1) !important;
        backdrop-filter: blur(10px) !important;
        animation: tableEntrance 0.8s var(--ease-smooth) both;
    }
    
    @keyframes tableEntrance {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Lovable Alert Messages */
    .stAlert {
        border-radius: 16px !important;
        border: none !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1) !important;
        margin: var(--space-md) 0 !important;
        animation: alertBounce 0.5s var(--ease-smooth) both;
    }
    
    @keyframes alertBounce {
        0% { transform: scale(0.9); opacity: 0; }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); opacity: 1; }
    }
    
    .stSuccess {
        background: linear-gradient(135deg, var(--success), var(--emerald)) !important;
        color: white !important;
        box-shadow: 0 0 20px rgba(34, 197, 94, 0.3) !important;
    }
    
    .stError {
        background: linear-gradient(135deg, var(--error), #dc2626) !important;
        color: white !important;
        box-shadow: 0 0 20px rgba(239, 68, 68, 0.3) !important;
    }
    
    .stWarning {
        background: linear-gradient(135deg, var(--warning), var(--warm-amber)) !important;
        color: white !important;
        box-shadow: 0 0 20px rgba(234, 179, 8, 0.3) !important;
    }
    
    .stInfo {
        background: linear-gradient(135deg, var(--sky-blue), var(--primary-blue)) !important;
        color: white !important;
        box-shadow: 0 0 20px rgba(14, 165, 233, 0.3) !important;
    }
    
    /* Premium Form Controls */
    .stSelectbox > div > div, .stMultiSelect > div > div {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 2px solid rgba(102, 126, 234, 0.2) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px) !important;
        transition: all var(--duration-normal) var(--ease-smooth) !important;
    }
    
    .stSelectbox > div > div:focus-within, .stMultiSelect > div > div:focus-within {
        border-color: var(--primary-blue) !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    .stNumberInput > div > div > input {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 2px solid rgba(102, 126, 234, 0.2) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px) !important;
        transition: all var(--duration-normal) var(--ease-smooth) !important;
    }
    
    .stNumberInput > div > div > input:focus {
        border-color: var(--primary-blue) !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Magical Expanders */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        backdrop-filter: blur(10px) !important;
        transition: all var(--duration-normal) var(--ease-smooth) !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(255, 255, 255, 0.15) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Plotly Chart Enhancement */
    .js-plotly-plot {
        border-radius: 16px !important;
        overflow: hidden !important;
        box-shadow: 
            0 4px 20px rgba(0,0,0,0.1),
            inset 0 1px 0 rgba(255,255,255,0.1) !important;
        animation: chartEntrance 1s var(--ease-smooth) both;
    }
    
    @keyframes chartEntrance {
        from {
            opacity: 0;
            transform: scale(0.95);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }
    
    /* Sidebar Text Styling */
    .css-1d391kg .markdown-text-container {
        color: rgba(255, 255, 255, 0.9) !important;
    }
    
    /* Status Indicators with Glow */
    .status-online {
        color: var(--success) !important;
        text-shadow: 0 0 10px rgba(34, 197, 94, 0.5) !important;
        animation: pulse 2s infinite !important;
    }
    
    .status-offline {
        color: var(--error) !important;
        text-shadow: 0 0 10px rgba(239, 68, 68, 0.5) !important;
        animation: pulse 2s infinite !important;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* Loading Spinner Magic */
    .stSpinner {
        text-align: center !important;
        color: var(--primary-blue) !important;
    }
    
    /* Checkbox Styling */
    .stCheckbox > label {
        color: rgba(255, 255, 255, 0.9) !important;
    }
    
    /* Responsive Breakpoints */
    @media (max-width: 768px) {
        :root {
            --text-hero: 2.5rem;
            --text-header: 1.5rem;
            --space-xl: 1.5rem;
            --space-2xl: 2rem;
        }
        
        .main .block-container {
            padding: var(--space-md);
            margin-top: var(--space-sm);
        }
    }
    
    /* Accessibility */
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

class LovableDashboard:
    """Breathtakingly Beautiful Air Quality Dashboard"""
    
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
    
    def render_magical_header(self):
        """Render breathtaking header with floating animations"""
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col2:
            st.markdown("""
                <div style="text-align: center; padding: var(--space-2xl) 0;">
                    <div style="display: flex; justify-content: center; align-items: center; margin-bottom: var(--space-lg);">
                        <div style="font-size: 4rem; margin-right: var(--space-md); animation: logoFloat 4s ease-in-out infinite;">🌍</div>
                        <h1 style="margin: 0;">
                            AirFlow Analytics
                        </h1>
                    </div>
                    <p style="color: rgba(255,255,255,0.95); margin: 0; font-size: 1.3rem; font-weight: 500; text-shadow: 0 2px 4px rgba(0,0,0,0.1); animation: subtitleGlow 2s ease-in-out infinite alternate;">
                        ✨ Breathtakingly Beautiful Environmental Intelligence ✨
                    </p>
                    <div style="width: 120px; height: 4px; background: var(--primary-gradient); margin: var(--space-lg) auto; border-radius: 2px; animation: barPulse 3s ease-in-out infinite; box-shadow: 0 0 20px rgba(102, 126, 234, 0.5);"></div>
                </div>
                
                <style>
                @keyframes logoFloat {
                    0%, 100% { transform: translateY(0px) rotate(0deg); }
                    25% { transform: translateY(-8px) rotate(2deg); }
                    50% { transform: translateY(-12px) rotate(0deg); }
                    75% { transform: translateY(-6px) rotate(-2deg); }
                }
                
                @keyframes subtitleGlow {
                    from { text-shadow: 0 2px 4px rgba(0,0,0,0.1), 0 0 20px rgba(255,255,255,0.1); }
                    to { text-shadow: 0 2px 4px rgba(0,0,0,0.1), 0 0 30px rgba(255,255,255,0.3); }
                }
                
                @keyframes barPulse {
                    0%, 100% { 
                        opacity: 1; 
                        transform: scaleX(1); 
                        box-shadow: 0 0 20px rgba(102, 126, 234, 0.5);
                    }
                    50% { 
                        opacity: 0.8; 
                        transform: scaleX(1.2); 
                        box-shadow: 0 0 40px rgba(118, 75, 162, 0.8);
                    }
                }
                </style>
            """, unsafe_allow_html=True)
        
        # Premium Status Cards
        col1, col2, col3, col4 = st.columns(4)
        
        status_cards = [
            {
                "icon": "🟢" if self.db and self.db.engine else "🔴",
                "title": "System Status",
                "value": "Online" if self.db and self.db.engine else "Offline",
                "class": "status-online" if self.db and self.db.engine else "status-offline",
                "color": "#22c55e" if self.db and self.db.engine else "#ef4444"
            },
            {
                "icon": "🚀",
                "title": "Environment",
                "value": "Production",
                "class": "status-online",
                "color": "#10b981"
            },
            {
                "icon": "⏰",
                "title": "Current Time",
                "value": datetime.now().strftime("%H:%M:%S"),
                "class": "",
                "color": "#667eea"
            },
            {
                "icon": "📦",
                "title": "Version",
                "value": "v3.0.0",
                "class": "",
                "color": "#764ba2"
            }
        ]
        
        for i, (col, card) in enumerate(zip([col1, col2, col3, col4], status_cards)):
            with col:
                st.markdown(f"""
                    <div style="
                        background: rgba(255,255,255,0.1); 
                        padding: var(--space-lg); 
                        border-radius: 16px; 
                        text-align: center; 
                        backdrop-filter: blur(15px); 
                        border: 1px solid rgba(255,255,255,0.2);
                        box-shadow: 0 4px 20px rgba(0,0,0,0.1), inset 0 1px 0 rgba(255,255,255,0.1);
                        transition: all var(--duration-normal) var(--ease-smooth);
                        cursor: pointer;
                        animation: cardStagger 0.8s var(--ease-smooth) both;
                        animation-delay: {i * 0.1}s;
                    " onmouseover="this.style.transform='translateY(-4px)'; this.style.boxShadow='0 8px 30px rgba(0,0,0,0.15)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 20px rgba(0,0,0,0.1)';">
                        <div style="font-size: 1.8rem; margin-bottom: var(--space-sm); animation: iconBob 3s ease-in-out infinite; animation-delay: {i * 0.2}s;">{card["icon"]}</div>
                        <div style="color: rgba(255,255,255,0.9); font-weight: 600; font-size: 0.85rem; margin-bottom: var(--space-xs);">{card["title"]}</div>
                        <div class="{card["class"]}" style="color: {card["color"]}; font-weight: 700; font-size: 1.1rem; font-family: 'JetBrains Mono', monospace;">{card["value"]}</div>
                    </div>
                    
                    <style>
                    @keyframes cardStagger {{
                        from {{ opacity: 0; transform: translateY(20px) scale(0.95); }}
                        to {{ opacity: 1; transform: translateY(0) scale(1); }}
                    }}
                    
                    @keyframes iconBob {{
                        0%, 100% {{ transform: translateY(0); }}
                        50% {{ transform: translateY(-3px); }}
                    }}
                    </style>
                """, unsafe_allow_html=True)

    def render_premium_sidebar(self):
        """Render magical sidebar navigation"""
        with st.sidebar:
            st.markdown("""
                <div style="text-align: center; padding: var(--space-xl) 0; margin-bottom: var(--space-xl);">
                    <div style="font-size: 2.5rem; margin-bottom: var(--space-sm); animation: compassSpin 8s linear infinite;">🧭</div>
                    <h2 style="color: rgba(255,255,255,0.95); margin: 0; font-size: 1.6rem; font-weight: 800; text-shadow: 0 2px 10px rgba(0,0,0,0.2);">Navigation</h2>
                    <div style="width: 60px; height: 3px; background: var(--primary-gradient); margin: var(--space-sm) auto; border-radius: 2px; box-shadow: 0 0 15px rgba(102, 126, 234, 0.6);"></div>
                </div>
                
                <style>
                @keyframes compassSpin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
                </style>
            """, unsafe_allow_html=True)
            
            # Magical Page Navigation
            pages = {
                'overview': ('🏠', 'Overview', '#10b981'),
                'monitoring': ('📈', 'Real-time Monitoring', '#0ea5e9'),
                'analytics': ('🔍', 'Advanced Analytics', '#f59e0b'),
                'alerts': ('🚨', 'Alert Management', '#ef4444'),
                'reports': ('📋', 'Reports & Export', '#8b5cf6'),
                'settings': ('⚙️', 'System Settings', '#64748b')
            }
            
            for key, (icon, label, color) in pages.items():
                is_current = st.session_state.current_page == key
                
                button_style = f"""
                    background: linear-gradient(135deg, {color}55, {color}77);
                    transform: translateX(8px);
                    box-shadow: 0 4px 20px {color}33;
                    border-left: 4px solid {color};
                """ if is_current else ""
                
                st.markdown(f"""
                    <div style="margin-bottom: var(--space-sm);">
                        <div style="
                            padding: var(--space-md) var(--space-lg); 
                            border-radius: 12px; 
                            {button_style} 
                            transition: all var(--duration-normal) var(--ease-smooth);
                            cursor: pointer;
                            border: 1px solid rgba(255,255,255,0.1);
                        " onmouseover="this.style.transform='translateX(12px)'; this.style.background='rgba(255,255,255,0.15)';" onmouseout="this.style.transform='{'translateX(8px)' if is_current else 'translateX(0)'}'; this.style.background='{'linear-gradient(135deg, ' + color + '55, ' + color + '77)' if is_current else 'transparent'}';">
                            <span style="font-size: 1.3rem; margin-right: var(--space-sm); filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));">{icon}</span>
                            <span style="font-weight: {'800' if is_current else '500'}; color: rgba(255,255,255,0.95); text-shadow: 0 1px 3px rgba(0,0,0,0.3);">{label}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"{icon} {label}", key=f"nav_{key}", use_container_width=True):
                    st.session_state.current_page = key
                    st.rerun()
            
            # Magical Controls Section
            st.markdown("""
                <div style="margin: var(--space-2xl) 0; height: 2px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent); border-radius: 1px;"></div>
                <div style="text-align: center; padding: var(--space-lg) 0;">
                    <div style="font-size: 1.8rem; margin-bottom: var(--space-sm); animation: controlPulse 2s ease-in-out infinite;">🎛️</div>
                    <h3 style="color: rgba(255,255,255,0.95); margin: 0; font-size: 1.4rem; font-weight: 700; text-shadow: 0 2px 10px rgba(0,0,0,0.2);">Mission Control</h3>
                </div>
                
                <style>
                @keyframes controlPulse {
                    0%, 100% { transform: scale(1); opacity: 0.8; }
                    50% { transform: scale(1.1); opacity: 1; }
                }
                </style>
            """, unsafe_allow_html=True)
            
            # Time Range Selector
            time_options = {
                '1h': '⚡ Last Hour',
                '24h': '🌅 Last 24 Hours', 
                '7d': '📅 Last 7 Days',
                '30d': '📊 Last 30 Days'
            }
            
            st.session_state.time_range = st.selectbox(
                "📊 Time Range",
                options=list(time_options.keys()),
                format_func=lambda x: time_options[x],
                index=1
            )
            
            # Magical Action Buttons
            st.markdown("""
                <div style="margin: var(--space-lg) 0;">
                    <h4 style="color: rgba(255,255,255,0.9); font-weight: 600; margin-bottom: var(--space-md); text-align: center;">⚡ Quick Actions</h4>
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Refresh", use_container_width=True):
                    st.cache_data.clear()
                    st.success("✨ Data magically refreshed!")
                    st.rerun()
            
            with col2:
                if st.button("🧪 Generate", use_container_width=True):
                    with st.spinner("🌟 Creating magical data..."):
                        try:
                            result = subprocess.run(
                                ["python", "sample_data_generator.py"],
                                capture_output=True,
                                text=True,
                                cwd="/app"
                            )
                            if result.returncode == 0:
                                st.success("🎉 Sample data generated with love!")
                                st.session_state.data_generated = True
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("⚠️ Generation spell failed")
                        except Exception as e:
                            st.error(f"⚠️ Magic error: {e}")
            
            # System Metrics Display
            st.markdown("""
                <div style="margin: var(--space-xl) 0; height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);"></div>
                <div style="text-align: center; padding: var(--space-md) 0;">
                    <div style="font-size: 1.5rem; margin-bottom: var(--space-xs);">💎</div>
                    <h4 style="color: rgba(255,255,255,0.9); margin: 0; font-weight: 600;">System Vitals</h4>
                </div>
            """, unsafe_allow_html=True)
            
            if self.db and self.db.engine:
                stats = self.db.get_data_quality_stats()
                if stats and 'air_quality' in stats:
                    aq_stats = stats['air_quality']
                    
                    # Animated metrics
                    measurements = aq_stats.get('total_measurements', 0)
                    cities = aq_stats.get('cities_count', 0)
                    
                    st.markdown(f"""
                        <div style="background: rgba(255,255,255,0.05); padding: var(--space-md); border-radius: 12px; margin: var(--space-sm) 0; border: 1px solid rgba(255,255,255,0.1);">
                            <div style="color: #10b981; font-weight: 700; font-size: 1.5rem; text-align: center; font-family: 'JetBrains Mono';">{measurements:,}</div>
                            <div style="color: rgba(255,255,255,0.8); font-size: 0.8rem; text-align: center; margin-top: 2px;">Total Measurements</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.05); padding: var(--space-md); border-radius: 12px; margin: var(--space-sm) 0; border: 1px solid rgba(255,255,255,0.1);">
                            <div style="color: #0ea5e9; font-weight: 700; font-size: 1.5rem; text-align: center; font-family: 'JetBrains Mono';">{cities}</div>
                            <div style="color: rgba(255,255,255,0.8); font-size: 0.8rem; text-align: center; margin-top: 2px;">Active Cities</div>
                        </div>
                    """, unsafe_allow_html=True)

    def get_time_hours(self):
        """Convert time range to hours"""
        mapping = {'1h': 1, '24h': 24, '7d': 168, '30d': 720}
        return mapping.get(st.session_state.time_range, 24)
    
    def render_overview_page(self):
        """Render breathtaking overview page"""
        st.header("🌟 Air Quality Universe")
        
        if not self.db:
            st.error("⚠️ Database constellation offline")
            return
        
        hours = self.get_time_hours()
        df = self.db.get_latest_air_quality_data(hours)
        
        if df.empty:
            st.warning("🌌 No cosmic data available. Generate some stellar data in the sidebar!")
            return
        
        # Magical Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        metrics = []
        if 'aqi' in df.columns:
            avg_aqi = df['aqi'].mean()
            aqi_status = "🟢 Excellent" if avg_aqi <= 50 else "🟡 Moderate" if avg_aqi <= 100 else "🔴 Concerning"
            aqi_color = "#22c55e" if avg_aqi <= 50 else "#eab308" if avg_aqi <= 100 else "#ef4444"
            metrics.append(("🌍", "Global AQI", f"{avg_aqi:.0f}", aqi_status, aqi_color))
        
        if 'city' in df.columns:
            cities = df['city'].nunique()
            metrics.append(("🏙️", "Active Cities", f"{cities}", f"Monitoring {cities} locations", "#10b981"))
        
        alerts = self.db.get_active_alerts()
        active_alerts = len(alerts) if not alerts.empty else 0
        alert_color = "#22c55e" if active_alerts == 0 else "#eab308" if active_alerts < 5 else "#ef4444"
        metrics.append(("🚨", "Active Alerts", f"{active_alerts}", "System monitoring", alert_color))
        
        measurements = len(df)
        metrics.append(("📊", "Data Points", f"{measurements:,}", f"Fresh insights", "#667eea"))
        
        for i, (col, (icon, title, value, subtitle, color)) in enumerate(zip([col1, col2, col3, col4], metrics)):
            with col:
                st.markdown(f"""
                    <div style="
                        background: linear-gradient(145deg, rgba(255,255,255,0.95), rgba(255,255,255,0.85));
                        border: 2px solid rgba(255,255,255,0.3);
                        border-radius: 20px;
                        padding: var(--space-xl);
                        text-align: center;
                        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                        backdrop-filter: blur(15px);
                        transition: all var(--duration-normal) var(--ease-smooth);
                        cursor: pointer;
                        animation: metricFloat 4s ease-in-out infinite;
                        animation-delay: {i * 0.3}s;
                    " onmouseover="this.style.transform='translateY(-12px) scale(1.03)'; this.style.boxShadow='0 20px 60px rgba(0,0,0,0.15)';" onmouseout="this.style.transform='translateY(0) scale(1)'; this.style.boxShadow='0 8px 32px rgba(0,0,0,0.1)';">
                        <div style="font-size: 3rem; margin-bottom: var(--space-md); filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));">{icon}</div>
                        <div style="color: {color}; font-weight: 900; font-size: 2.5rem; font-family: 'JetBrains Mono'; margin-bottom: var(--space-xs); text-shadow: 0 2px 4px rgba(0,0,0,0.1);">{value}</div>
                        <div style="color: #1e293b; font-weight: 700; font-size: 1rem; margin-bottom: var(--space-xs);">{title}</div>
                        <div style="color: #64748b; font-size: 0.85rem; font-weight: 500;">{subtitle}</div>
                    </div>
                    
                    <style>
                    @keyframes metricFloat {{
                        0%, 100% {{ transform: translateY(0); }}
                        50% {{ transform: translateY(-6px); }}
                    }}
                    </style>
                """, unsafe_allow_html=True)
        
        # Beautiful Charts Section
        st.markdown("""
            <div style="margin: var(--space-2xl) 0;">
                <h2 style="text-align: center; margin-bottom: var(--space-xl);">📈 Environmental Intelligence Dashboard</h2>
            </div>
        """, unsafe_allow_html=True)
        
        if 'aqi' in df.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                # AQI Distribution with custom styling
                fig_hist = px.histogram(
                    df, x='aqi', nbins=30,
                    title="🌈 AQI Distribution Spectrum",
                    labels={'aqi': 'Air Quality Index', 'count': 'Frequency'},
                    color_discrete_sequence=['#667eea']
                )
                fig_hist.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Inter", color='#1e293b'),
                    title_font=dict(size=18, family="Inter"),
                    showlegend=False
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with col2:
                # Top cities with gradient colors
                if 'city' in df.columns:
                    city_aqi = df.groupby('city')['aqi'].mean().reset_index()
                    city_aqi = city_aqi.sort_values('aqi', ascending=False).head(10)
                    
                    fig_bar = px.bar(
                        city_aqi, x='aqi', y='city',
                        orientation='h', title="🏆 Top Cities by AQI",
                        labels={'aqi': 'Average AQI', 'city': 'City'},
                        color='aqi',
                        color_continuous_scale=['#22c55e', '#eab308', '#ef4444']
                    )
                    fig_bar.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(family="Inter", color='#1e293b'),
                        title_font=dict(size=18, family="Inter")
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
        
        # Time Series Magic
        if 'timestamp' in df.columns and 'aqi' in df.columns:
            st.subheader("⏳ Temporal AQI Journey")
            
            df_sorted = df.sort_values('timestamp')
            fig_line = px.line(
                df_sorted.head(500), x='timestamp', y='aqi',
                title="🌊 AQI Flow Through Time",
                labels={'timestamp': 'Time Portal', 'aqi': 'Air Quality Index'},
                color_discrete_sequence=['#667eea']
            )
            fig_line.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter", color='#1e293b'),
                title_font=dict(size=20, family="Inter")
            )
            fig_line.update_traces(line=dict(width=3))
            st.plotly_chart(fig_line, use_container_width=True)
        
        # Premium Data Table
        st.subheader("💎 Recent Cosmic Measurements")
        
        display_cols = ['city', 'country', 'aqi', 'pm25', 'pm10', 'timestamp']
        available_cols = [col for col in display_cols if col in df.columns]
        
        if available_cols:
            recent_data = df[available_cols].head(20)
            if 'timestamp' in recent_data.columns:
                recent_data['timestamp'] = pd.to_datetime(recent_data['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(recent_data, use_container_width=True, hide_index=True)

    def run(self):
        """Launch the lovable dashboard"""
        inject_lovable_css()
        self.render_magical_header()
        self.render_premium_sidebar()
        
        # Page routing with staggered animations
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
            st.error("🔮 Page not found in this universe")
        
        # Magical Footer
        st.markdown("""
            <div style="margin-top: var(--space-2xl); padding: var(--space-2xl) 0; background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.08)); border-radius: 24px; backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.1);">
                <div style="text-align: center;">
                    <div style="display: flex; justify-content: center; align-items: center; margin-bottom: var(--space-lg);">
                        <div style="font-size: 2rem; margin-right: var(--space-sm); animation: sparkle 3s infinite;">✨</div>
                        <div style="color: rgba(255,255,255,0.95); font-size: 1.2rem; font-weight: 600;">
                            © 2024 AirFlow Analytics
                        </div>
                        <div style="font-size: 2rem; margin-left: var(--space-sm); animation: sparkle 3s infinite 1.5s;">✨</div>
                    </div>
                    <div style="color: rgba(255,255,255,0.8); font-size: 1rem; margin-bottom: var(--space-lg);">
                        Breathtakingly Beautiful Environmental Intelligence Platform
                    </div>
                    <div style="display: flex; justify-content: center; gap: var(--space-xl); flex-wrap: wrap;">
                        <div style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">🚀 Next-Gen UI</div>
                        <div style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">⚡ Real-time Magic</div>
                        <div style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">💎 Premium Experience</div>
                        <div style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">🌟 Built with Love</div>
                    </div>
                </div>
            </div>
            
            <style>
            @keyframes sparkle {
                0%, 100% { 
                    opacity: 1; 
                    transform: scale(1) rotate(0deg); 
                }
                25% { 
                    opacity: 0.7; 
                    transform: scale(1.2) rotate(90deg); 
                }
                50% { 
                    opacity: 1; 
                    transform: scale(0.8) rotate(180deg); 
                }
                75% { 
                    opacity: 0.9; 
                    transform: scale(1.1) rotate(270deg); 
                }
            }
            </style>
        """, unsafe_allow_html=True)

# Main execution
if __name__ == "__main__":
    dashboard = LovableDashboard()
    dashboard.run()