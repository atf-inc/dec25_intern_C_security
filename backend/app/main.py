# backend/app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings, configure_dotenv
from app.db.session import init_db
from app.api.v1.routes_upload import router as upload_router
from app.api.v1.routes_analyze import router as analyze_router
from app.api.v1.routes_misc import router as misc_router

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# load .env early
configure_dotenv()

from app.api.v1 import routes_voice

# Initialize rate limiter (in-memory storage)
limiter = Limiter(key_func=get_remote_address)

def create_application():
    app = FastAPI(title="ATF CyberX - Phishing Detection MVP")
    
    # Add rate limiter to app state
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Add CORS middleware - MUST be added BEFORE including routers
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",  # Vite dev server
            "http://127.0.0.1:5173",  # Alternative localhost format
            "http://localhost:5174",  # Vite backup port
            "http://127.0.0.1:5174",  # Alternative localhost format
            "http://localhost:3000",  # React dev server
            "http://localhost:3002",  # Alternative React port
            "*"  # Allow all origins for development
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(upload_router)
    app.include_router(analyze_router)
    app.include_router(misc_router)

    @app.on_event("startup")
    def on_startup():
        init_db()

    app.include_router(routes_voice.router, prefix="/api/v1")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app

app = create_application()
