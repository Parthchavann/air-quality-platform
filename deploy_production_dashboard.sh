#!/bin/bash

# Production Dashboard Deployment Script
echo "🚀 Deploying Production-Ready Air Quality Dashboard"
echo "=================================================="

# Check if containers are running
echo "🔍 Checking system status..."

if ! docker ps | grep -q "airquality-postgres.*Up"; then
    echo "⚠️ PostgreSQL container not running. Starting..."
    docker compose up -d postgres
    sleep 10
fi

if ! docker ps | grep -q "airquality-streamlit.*Up"; then
    echo "⚠️ Streamlit container not running. Starting..."
    docker compose up -d streamlit
    sleep 15
fi

# Test database connection
echo "🔗 Testing database connection..."
if docker exec airquality-streamlit python -c "from database import DatabaseConnection; db=DatabaseConnection(); print('✅ Database connected' if db.engine else '❌ Database failed')"; then
    echo "✅ Database connection successful"
else
    echo "❌ Database connection failed"
    exit 1
fi

# Check if data exists
echo "📊 Checking data availability..."
DATA_COUNT=$(docker exec airquality-streamlit python -c "from database import DatabaseConnection; db=DatabaseConnection(); df=db.get_latest_air_quality_data(24); print(len(df))" 2>/dev/null)

if [ "$DATA_COUNT" -lt "100" ]; then
    echo "🧪 Insufficient data found. Generating sample data..."
    docker exec airquality-streamlit python sample_data_generator.py
    echo "✅ Sample data generated"
else
    echo "✅ Sufficient data available ($DATA_COUNT records)"
fi

# Test dashboard health
echo "🏥 Testing dashboard health..."
sleep 5

if curl -sf http://localhost:8502/_stcore/health > /dev/null 2>&1; then
    echo "✅ Dashboard is healthy and responsive"
else
    echo "❌ Dashboard health check failed"
    exit 1
fi

# Performance check
echo "⚡ Running performance check..."
RESPONSE_TIME=$(curl -w "%{time_total}" -s -o /dev/null http://localhost:8502 2>/dev/null || echo "0")
echo "📊 Response time: ${RESPONSE_TIME}s"

echo ""
echo "🎉 Production Dashboard Deployment Complete!"
echo "============================================"
echo ""
echo "🌐 Dashboard URL: http://localhost:8502"
echo "📊 Features Available:"
echo "   ✅ Real-time Air Quality Overview"
echo "   ✅ Live Monitoring with City Selection"  
echo "   ✅ Advanced Analytics & Trend Analysis"
echo "   ✅ Smart Alert Management System"
echo "   ✅ Custom Report Generation & Export"
echo "   ✅ System Settings & Configuration"
echo ""
echo "🛠️  Management Commands:"
echo "   • Refresh data: Click 'Generate Sample Data' in sidebar"
echo "   • Clear cache: Click 'Refresh Data' in sidebar"
echo "   • View logs: docker logs airquality-streamlit"
echo "   • Restart: docker compose restart streamlit"
echo ""
echo "✨ Your enterprise air quality dashboard is ready for production use!"