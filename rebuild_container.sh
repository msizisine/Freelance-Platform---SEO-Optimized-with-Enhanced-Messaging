#!/bin/bash

echo "Rebuilding Docker container with updated code..."

# Stop the containers
echo "Stopping containers..."
docker-compose down

# Rebuild the web service with no cache to ensure fresh build
echo "Rebuilding web service..."
docker-compose build --no-cache web

# Start the containers
echo "Starting containers..."
docker-compose up -d

echo "Container rebuild complete. Checking status..."
docker-compose ps
