from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app import settings
from connection import async_engine, Base
import chat

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # Startup: Adatbázis táblák létrehozása aszinkron módon, ha nem léteznek
    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: Kapcsolatok biztonságos lezárása
    await async_engine.dispose()

app = FastAPI(
    title="Biztonságos LLM Chat API Gateway",
    version="1.0.0",
    lifespan=app_lifespan
)

# CORS konfiguráció — Kiberbiztonsági szigorítás wildcad (*) ellen
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Authorization", "Content-Type"],
)

# API Útvonalak regisztrálása
app.include_router(chat.router, prefix="/api/v1")

@app.get("/health", tags=["Rendszer"])
async def health_check():
    return {"status": "healthy", "architecture": "3-tier-async"}

if __name__ == "__main__":
    import uvicorn
    # Gyártási környezetben javasolt a worker-szám és a logolás finomhangolása
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)