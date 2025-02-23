#!/bin/bash

# Update package lists and install mtr
sudo apt-get update && sudo apt-get install -y mtr

echo "Starting FastAPI app..."
uvicorn main:app --host 0.0.0.0 --port $PORT
