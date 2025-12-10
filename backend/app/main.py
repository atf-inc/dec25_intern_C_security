from fastapi import FastAPI
from app.core.config import settings

def create_application():
    app = FastAPI(title="CyberX Backend", debug=settings.debug)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app

app = create_application()
