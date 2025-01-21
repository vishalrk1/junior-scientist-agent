from buddy.agents import AnalyzerAgent
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from database import Database
from auth.router import router as auth_router
@asynccontextmanager
async def lifespan(app: FastAPI):
    await Database.connect_db()
    yield
    await Database.close_db()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    if await Database.check_connection():
        return {"status": "healthy", "database": "connected"}
    raise HTTPException(status_code=503, detail="Database connection failed")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=auth_router, prefix="/auth", tags=["auth"])