#!/bin/bash

# Premium Air Quality Dashboard Deployment Script
# This script sets up and deploys the beautiful premium dashboard

set -e

echo "🌍 Deploying Premium Air Quality Dashboard..."
echo "=============================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Stop existing services
echo "🛑 Stopping existing services..."
docker compose down streamlit

# Build and start the premium dashboard
echo "🔨 Building premium dashboard container..."
docker compose build streamlit

echo "🚀 Starting premium dashboard..."
docker compose up -d streamlit postgres

# Wait for services to be ready
echo "⏳ Waiting for services to initialize..."
sleep 15

# Populate with sample data
echo "📊 Generating beautiful sample data..."
docker exec airquality-streamlit python sample_data_generator.py

# Check service status
echo ""
echo "🔍 Checking service status..."
echo "================================"

if docker compose ps streamlit | grep -q "Up"; then
    echo "✅ Premium Dashboard: Running"
else
    echo "❌ Premium Dashboard: Not running"
fi

if docker compose ps postgres | grep -q "Up"; then
    echo "✅ PostgreSQL Database: Running"
else
    echo "❌ PostgreSQL Database: Not running"
fi

echo ""
echo "🎉 Premium Air Quality Dashboard is ready!"
echo "=========================================="
echo ""
echo "🌐 Dashboard URL: http://localhost:8502"
echo ""
echo "✨ Features Available:"
echo "   🏠 Home - Global overview with real-time metrics"
echo "   🗺️ Map View - Interactive world map with city AQI"
echo "   📊 Analytics - Advanced charts and comparisons"
echo "   🚨 Alerts - Smart alert management system"
echo "   ⚙️ Settings - Customizable preferences"
echo ""
echo "📱 Mobile Responsive: Perfect on phones, tablets & desktop"
echo "🎨 Premium Design: Enterprise-grade UI/UX"
echo "⚡ Real-time Updates: Live data refresh every 60 seconds"
echo ""
echo "🎯 Sample Data Generated:"
echo "   • 15 global cities with 7 days of hourly data"
echo "   • 2,500+ air quality measurements"
echo "   • 2,500+ weather data points"
echo "   • Smart pollution alerts"
echo ""
echo "💡 Pro Tip: Try different pages, hover effects, and interactive charts!"
echo ""
echo "🔄 To regenerate sample data: docker exec airquality-streamlit python sample_data_generator.py"
echo "🛑 To stop dashboard: docker compose stop streamlit"
echo ""

# Check if dashboard is accessible
if curl -s http://localhost:8502 > /dev/null; then
    echo "✅ Dashboard is accessible at http://localhost:8502"
    echo ""
    echo "🎊 SUCCESS! Your premium dashboard is live and beautiful!"
else
    echo "⚠️  Dashboard may still be starting. Please wait a moment and try:"
    echo "   http://localhost:8502"
fi

echo ""
echo "📚 Enjoy your world-class air quality monitoring platform! 🌟"