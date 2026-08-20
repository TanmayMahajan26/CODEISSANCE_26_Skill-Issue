from fastapi import FastAPI
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="IdentityForge - Financial Customer 360 & Next-Best-Opportunity Engine",
)

@app.get("/health")
def health_check():
    return {"status": "ok", "app_name": settings.APP_NAME}
