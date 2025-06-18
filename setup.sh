#!/bin/bash

# DelayCompanion Setup Script

echo "Setting up DelayCompanion..."

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Set up DynamoDB tables and load sample data
echo "Setting up DynamoDB tables and loading sample data..."
python main.py --setup

echo "Setup complete!"
echo "To run the application, use: python main.py"
echo "To run with debug logging: python main.py --debug"
