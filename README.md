# Shelfstone

## Overview

This project provides a containerized web application for interacting with a Calibre e-book library. It consists of:

*   A **Shelfstone Server** (built with FastAPI and Python) that uses Calibre's command-line tools (`calibredb`, `ebook-convert`, etc.) to manage and access e-book data.
*   A **Shelfstone Web** (built with SvelteKit) that communicates with the backend API to provide a user-friendly experience.

The entire application is designed to be run using Docker and Docker Compose, simplifying setup and deployment.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

*   [Docker](https://docs.docker.com/get-docker/)
*   [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)

## Setup & Running

1.  **Clone the Repository (if you haven't already):**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create Data Directories:**
    For data persistence (your Calibre library and configuration), you need to create two directories in the root of this project:
    ```bash
    mkdir calibre_library_data
    mkdir calibre_config_data
    ```
    These directories will be mounted into the backend container, ensuring your data is saved on your host machine and persists across container restarts.

3.  **Build and Start the Application:**
    Navigate to the root directory of the project (where the `docker-compose.yml` file is located) and run:
    ```bash
    docker-compose up -d --build
    ```
    *   `--build`: Forces Docker to build the images from the Dockerfiles (recommended for the first run or after code changes).
    *   `-d`: Runs the containers in detached mode (in the background).

    On the first run, Docker will download the base images (Python, Node, Nginx) and then build the application containers. This process might take a few minutes depending on your internet connection and system performance.

## Accessing the Application

Once the containers are up and running:

*   **Frontend Web Interface:** Open your web browser and go to:
    [`http://localhost:6464`](http://localhost:6464)

*   **Backend API Documentation (Swagger UI):** The backend API provides interactive documentation. You can access it at:
    [`http://localhost:8001/docs`](http://localhost:8001/docs)
    This is useful for understanding the API endpoints or for direct API interaction if needed.

## Data Persistence

*   Your Calibre e-book library data will be stored in the `./calibre_library_data` directory on your host machine.
*   Calibre's internal configuration files will be stored in the `./calibre_config_data` directory on your host machine.

This setup uses **bind mounts**, meaning these host directories are directly mapped into the container. This is beneficial because:
*   Your data is safe even if you stop or remove the containers.
*   You can easily access or back up your Calibre library from your host system.

**Alternative: Named Volumes**
The `docker-compose.yml` file includes comments on how to switch to Docker-managed **named volumes** instead of bind mounts. Named volumes can be easier to manage in some scenarios and might avoid potential file permission issues on Linux systems. If you prefer named volumes, please see the instructions in the `docker-compose.yml` file.

## Stopping the Application

To stop and remove the application containers, navigate to the project root directory and run:
```bash
docker-compose down
```
This command will stop the containers. If you also want to remove the volumes (though generally not desired for the data volumes if you want to keep your library), you can add the `-v` flag: `docker-compose down -v`.

## Development & Logs

*   **Viewing Logs:** To see the logs from the running containers (useful for troubleshooting):
    ```bash
    docker-compose logs -f shelfstone-server
    docker-compose logs -f shelfstone-web
    # To see logs for all services:
    docker-compose logs -f
    ```
    Press `Ctrl+C` to stop tailing the logs.

*   **Rebuilding Images:** If you make changes to the application code (Shelfstone Server or Shelfstone Web) or the Dockerfiles, you'll need to rebuild the Docker images:
    ```bash
    docker-compose up -d --build
    ```

## Troubleshooting

*   **Port Conflicts:** If ports `6464` or `8001` are already in use on your system, you can change them in the `docker-compose.yml` file (the host-side port mapping, e.g., `"NEW_PORT:6336"`).
*   **Calibre Issues:** If the Shelfstone Server has issues related to Calibre itself, check the logs of the `shelfstone-server` service. Ensure Calibre is correctly installed in the Docker image (this should be handled by the `calibre_api/Dockerfile`).
*   **Frontend Build Issues:** If Shelfstone Web fails to build, check the logs during the `docker-compose up --build` process. It might indicate missing dependencies or build script errors.

This `README.md` should provide a good starting point for users.
