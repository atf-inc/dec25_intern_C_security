from fastapi import FastAPI
from app.core.config import settings

from app.api.v1 import routes_voice

def create_application():
    app = FastAPI(title="CyberX Backend", debug=settings.debug)

    app.include_router(routes_voice.router, prefix="/api/v1")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app

app = create_application()
