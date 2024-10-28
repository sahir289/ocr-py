
#!/bin/bash

# Define variables
PROJECT_DIR="/home/ubuntu/ocr-py-new/ocr-py"
MAIN_FILE="main.py"
REQUIREMENTS_FILE="$PROJECT_DIR/requirements.txt"
PYTHON_CMD="/usr/bin/python3"
VENV_DIR="$PROJECT_DIR/venv"
AWS_REGION="us-east-1"  # Set your preferred region here

# Update system packages
echo "***** Updating system packages *****"
sudo apt-get update -y

# Install Python3, pip, and virtualenv if they are not installed
echo "***** Installing Python3, pip, and virtualenv *****"
sudo apt-get install python3 python3-pip python3-venv -y

# Navigate to the project directory
cd "$PROJECT_DIR" || { echo "Project directory not found!"; exit 1; }

# Create a virtual environment
echo "***** Creating Python virtual environment *****"
python3 -m venv "$VENV_DIR"

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Install Python dependencies from requirements.txt
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "***** Installing dependencies from requirements.txt *****"
    pip install -r "$REQUIREMENTS_FILE"
else
    echo "requirements.txt not found in the project directory!"
    deactivate
    exit 1
fi

# Specify AWS region for any AWS commands
export AWS_DEFAULT_REGION=$AWS_REGION

# Start FastAPI server by calling the main file directly
echo "***** Starting FastAPI server *****"
python "$MAIN_FILE"

# Deactivate virtual environment when done
deactivate
