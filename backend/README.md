# ATF CyberX - Backend

FastAPI backend for ATF CyberX.

## Setup

```bash
pip install -r requirements.txt
```

## Development

```bash
uvicorn app.main:app --reload --port 8000
```

The API will run on http://localhost:8000

API documentation available at http://localhost:8000/docs

## Features

- Phishing Email Analysis API
- Voice Deepfake Detection API
- SQLite Database for scan history
- Placeholder ML models (to be replaced with real models)

## Tech Stack

- FastAPI
- SQLAlchemy
- Pydantic
- SQLite
- Python 3.9+

## Project Structure

```
backend/
├── app/
│   ├── api/v1/          # API routes
│   ├── core/            # Configuration
│   ├── db/              # Database layer
│   ├── ml/              # ML models
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   └── utils/           # Utilities
├── tests/               # Tests
└── requirements.txt     # Dependencies
```
