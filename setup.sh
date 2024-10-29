#!/bin/bash

# Variables
IMAGE_NAME="ocr_image"
CONTAINER_NAME="ocr_image_container"
PORT_MAPPING="8000:8000"  # Map host port 8000 to container port 8000, modify if needed
DOCKERFILE_PATH="./Dockerfile"  # Assuming Dockerfile is in the current directory
MAIN_FILE="main.py"  # The entry point for your Python application

# Function to install Docker and its dependencies
install_docker() {
    echo "Installing Docker and its dependencies..."

    # Update package list
    sudo apt-get update

    # Install necessary packages
    sudo apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release \
        apt-transport-https

    # Add Docker’s official GPG key and set up the stable repository
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker Engine
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io

    # Start Docker service
    sudo systemctl start docker
    sudo systemctl enable docker
}

# Function to check if Docker is installed
check_docker_installed() {
    if ! [ -x "$(command -v docker)" ]; then
        echo "Docker is not installed. Installing Docker..."
        install_docker
    else
        echo "Docker is already installed."
    fi
}

# Function to build the Docker image
build_docker_image() {
    echo "Building Docker image..."
    docker build -t $IMAGE_NAME -f $DOCKERFILE_PATH .

    if [ $? -ne 0 ]; then
        echo "Docker build failed. Exiting."
        exit 1
    fi
    echo "Docker image built successfully."
}

# Function to run the Docker container
run_docker_container() {
    # Stop and remove any existing container with the same name
    if [ "$(docker ps -a -q -f name=$CONTAINER_NAME)" ]; then
        echo "Stopping and removing existing container..."
        docker rm -f $CONTAINER_NAME
    fi

    # Run the new container
    echo "Running Docker container..."
    docker run --name $CONTAINER_NAME -p $PORT_MAPPING $IMAGE_NAME

    if [ $? -eq 0 ]; then
        echo "Docker container started successfully."
        echo "Application is running. You can access it at http://localhost:$PORT_MAPPING"
    else
        echo "Failed to start Docker container. Exiting."
        exit 1
    fi
}

# Main script
check_docker_installed
build_docker_image
run_docker_container
