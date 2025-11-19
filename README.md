# Sports Stats Dashboard

A FastAPI-based sports analytics dashboard that leverages TheSportsDB API for match data and integrates multiple Large Language Models (OpenAI GPT, Google Gemini, and Groq) for intelligent match analysis. Features a web-based UI, robust error handling with mock data fallbacks, and Redis caching for performance.

## Features

- **FastAPI Framework**: High-performance async API for sports data analysis
- **Multi-LLM Analysis**: Compare insights from OpenAI GPT-4, Google Gemini, and Groq models
- **Web Interface**: User-friendly HTML/CSS/JS frontend for easy interaction
- **Dockerized**: Containerized deployment with Docker Compose
- **Redis Caching**: Performance optimization for LLM responses
- **Mock Data Fallbacks**: Reliable operation even when external APIs are unavailable
- **Structured Logging**: JSON-formatted logs for production monitoring
- **Health Checks**: Application status monitoring endpoints
- **Comprehensive Testing**: Unit tests with pytest and coverage reporting
- **CI/CD Integration**: Automated testing and Docker builds using GitHub Actions

## Prerequisites

- **Python**: Version 3.11 or higher
- **Docker**: Installed and running (for containerized deployment)
- **Redis**: Running instance (optional, for caching)

## Installation

1. Clone the repository:

   git clone https://github.com/MichaelcodP/sports-stats-dashboard.git
   cd sports-stats-dashboard

2. Create and activate virtual environment:

   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install dependencies:

   pip install -r requirements.txt

4. Set environment variables:
   export THESPORTSDB_API_KEY="your_thesportsdb_api_key"  # Get from https://www.thesportsdb.com/api.php
   export OPENAI_API_KEY="your_openai_api_key"
   export GEMINI_API_KEY="your_gemini_api_key"
   export GROQ_API_KEY="your_groq_api_key"
   export REDIS_URL="redis://localhost:6379"  # Optional, for caching

## Running the Application

### Locally

1. Start the application:

   uvicorn app.main:app --reload

2. Access the application:
   - **Web Interface**: http://127.0.0.1:8000
   - **API Documentation**: http://127.0.0.1:8000/docs

### With Docker

1. Build and run with Docker Compose:

   docker-compose up --build

2. Access the application:
   - **Web Interface**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs

## API Endpoints

### Health & Status

- **`GET /health`**: Application health check

### Team Analysis

- **`GET /api/analyze/team/{team_name}`**: Analyze last 5 matches of a team with LLM insights
- **`GET /api/analyze/team/id/{team_id}`**: Analyze team matches by team ID

### Match Analysis

- **`GET /api/analyze/all-models/{team1}/{team2}`**: Compare analysis from all LLM providers for the latest match between two teams
- **`GET /api/analyze/vs/{team1}/{team2}`**: Get LLM analysis for the latest match between two teams
- **`GET /api/analyze/match/{match_id}`**: Analyze a specific match by its ID
- **`GET /api/analyze/h2h/{team1_name}/{team2_name}`**: Get head-to-head statistics between two teams

### Metrics

- **`GET /api/metrics`**: Get overall system metrics (total matches, teams, goals)
- **`GET /api/metrics/{team_name}`**: Get detailed metrics for a specific team
  - Query Parameters:
    - `opponent`: Filter by specific opponent
    - `match_type`: Filter by `home` or `away` matches
    - `last_n`: Number of recent matches to analyze (default: 5)

### Web Interface

- **`GET /`**: Main web application interface for interactive analysis

## Web Interface Features

The web dashboard provides:

- **Team Analysis**: Analyze recent performance of any Premier League team
- **All Models Comparison**: Compare insights from OpenAI, Gemini, and Groq for match analysis
- **Metrics Dashboard**: View system-wide statistics and team-specific metrics

## Testing

Run the test suite with pytest:

Run tests with coverage:

```bash
pytest --cov=app --cov-report=html
```

## Architecture

- **Backend**: FastAPI with async/await patterns
- **Data Sources**: TheSportsDB API with mock data fallbacks
- **LLM Integration**: Multi-provider orchestration with caching
- **Frontend**: Vanilla HTML/CSS/JS with Fetch API
- **Caching**: Redis for LLM response caching
- **Testing**: pytest with async support
- **Containerization**: Docker with multi-stage builds
