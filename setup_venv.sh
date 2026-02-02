#!/bin/bash
# Setup virtual environment for IDS2 SOC project

cd /home/tor/Downloads/oi/python_env

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

echo "Virtual environment created and dependencies installed."
echo "To activate: source python_env/venv/bin/activate"
echo "To deactivate: deactivate"