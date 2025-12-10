from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging_config import setup_logging
from app.db.session import init_db, engine, Base
from app.api.v1.routes_upload import router as upload_router
from app.api.v1.routes_phishing import router as phishing_router
from app.core.config import settings

def create_application():
    setup_logging()
    app = FastAPI(title="ATF CyberX Backend", debug=settings.debug)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for development
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    @app.on_event("startup")
    def on_startup():
        init_db()

    @app.get("/health")
    def health():
        return {"status": "ok"}
    
    # Include API routes
    app.include_router(upload_router, prefix="/api/v1")
    app.include_router(phishing_router, prefix="/api/v1")
    
    return app

app = create_application()
