#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define the Python version and main file
PYTHON_VERSION=python3  # Change this if you want to use a specific Python version
MAIN_FILE=main.py        # Change this to the name of your main Python file
VENV_DIR=venv            # Directory for the virtual environment
AWS_REGION=us-east-1     # Set your AWS region here

# Create a virtual environment
echo "Creating a virtual environment in the directory: $VENV_DIR"
$PYTHON_VERSION -m venv $VENV_DIR

# Activate the virtual environment
echo "Activating the virtual environment"
source $VENV_DIR/bin/activate

# Upgrade pip
echo "Upgrading pip"
pip install --upgrade pip

# Install required packages from requirements.txt
echo "Installing requirements from requirements.txt"
pip install -r requirements.txt

# Export the AWS region as an environment variable
export AWS_REGION

# Optionally print the AWS region to confirm it's set
echo "AWS Region is set to: $AWS_REGION"

# Run the main Python script
echo "Running the main Python script: $MAIN_FILE"
$PYTHON_VERSION $MAIN_FILE

# Deactivate the virtual environment (optional)
deactivate
