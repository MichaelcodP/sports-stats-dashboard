# Sports Stats Dashboard

A FastAPI-based application for analyzing sports matches using external APIs and machine learning models. This project is containerized with Docker and includes CI/CD workflows for automated testing and deployment.

## Features

- **FastAPI Framework**: High-performance API for sports data analysis.
- **Dockerized**: Easily deployable with Docker and Docker Compose.
- **Structured Logging**: JSON-formatted logs for better observability.
- **Health Check Endpoint**: `/health` endpoint to monitor application status.
- **Metrics Endpoint**: `/metrics/{team_name}` to analyze team performance.
- **CI/CD Integration**: Automated testing and Docker builds using GitHub Actions.

## Prerequisites

- **Python**: Version 3.11 or higher.
- **Docker**: Installed and running.

## Installation

1. Clone the repository:
   git clone https://github.com/MichaelcodP/sports-stats-dashboard.git
   cd sports-stats-dashboard

2. Install dependencies:
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt

3. Set environment variables:
   - `SPORTS_API_KEY`: Your TheSportsDB API key.
   - `TEAM_NAMES`: Comma-separated list of team names to fetch data for (e.g., `Arsenal,Chelsea,Liverpool`).

## Running the Application

### Locally

1. Start the application:
   uvicorn app.main:app --reload

2. Access the API at `http://127.0.0.1:8000`.

### With Docker

1. Build and run the Docker container:
   docker-compose up --build

2. Access the API at `http://localhost:8000`.

## Endpoints

- **`GET /health`**: Returns the application status.
- **`GET /metrics/{team_name}`**: Analyze team performance.
  - Query Parameters:
    - `opponent`: Filter metrics by a specific opponent.
    - `match_type`: Filter by `home` or `away` matches.

## Testing

Run tests with `pytest`:
pytest --maxfail=2 --disable-warnings