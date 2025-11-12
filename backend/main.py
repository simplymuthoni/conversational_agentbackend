from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import research, sms
from .config import settings


app = FastAPI(title="Research-Augmented Agent API")


app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
)


app.include_router(research.router, prefix="/api")
app.include_router(sms.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "env": settings.APP_ENV}
