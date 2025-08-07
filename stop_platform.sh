#!/bin/bash

# Air Quality Monitoring Platform Stop Script

set -e

echo "🛑 Stopping Air Quality Monitoring Platform..."

# Stop data ingestion processes
echo "   Stopping data ingestion processes..."
pkill -f "data_ingestion_pipeline.py" 2>/dev/null || true
pkill -f "air_quality_processor.py" 2>/dev/null || true

# Stop Docker containers gracefully
echo "   Stopping Docker containers..."
docker-compose down

# Optional: Remove volumes (uncomment if you want to clear all data)
# read -p "🗑️  Remove all data volumes? (y/n): " -n 1 -r
# echo
# if [[ $REPLY =~ ^[Yy]$ ]]; then
#     echo "   Removing data volumes..."
#     docker-compose down -v
#     docker volume prune -f
# fi

# Clean up temporary files
echo "   Cleaning up temporary files..."
rm -rf /tmp/spark-checkpoints/* 2>/dev/null || true

echo "✅ Air Quality Monitoring Platform stopped successfully!"
echo ""
echo "📋 To restart: ./start_platform.sh"
echo "🔧 To reset all data: docker-compose down -v && docker volume prune -f"