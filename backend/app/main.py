# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings, configure_dotenv
from app.db.session import init_db
from app.api.v1.routes_upload import router as upload_router
from app.api.v1.routes_analyze import router as analyze_router
from app.api.v1.routes_misc import router as misc_router

# load .env early
configure_dotenv()

def create_application():
    app = FastAPI(title="ATF CyberX - Phishing Detection MVP")

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS + ["http://localhost:3000", "http://localhost:3002"],
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

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app

app = create_application()
