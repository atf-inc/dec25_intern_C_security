from fastapi import FastAPI
from app.core.logging_config import setup_logging
from app.db.session import init_db
from app.api.v1.routes_upload import router as upload_router
from app.core.config import settings

def create_application():
    setup_logging()
    app = FastAPI(title="CyberX Backend", debug=settings.debug)
    
    app.include_router(upload_router)
    
    @app.on_event("startup")
    def on_startup():
        init_db()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app

app = create_application()
