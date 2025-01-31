from buddy.agents import AnalyzerAgent
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from database import Database
from auth.router import router as auth_router
from project.router import router as project_router
from agent.router import router as agents_router
from rag.routes import router as rag_router
from api import workflow

@asynccontextmanager
async def lifespan(app: FastAPI):
    await Database.connect_db()
    yield
    await Database.close_db()

app = FastAPI(title="Junior Data Scientist Agent API", lifespan=lifespan)

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

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(project_router, prefix="/projects", tags=["Projects"])
app.include_router(agents_router, prefix="/api", tags=["agents"])
app.include_router(rag_router, prefix="/rag", tags=["RAG"])
app.include_router(workflow.router, prefix="/workflow")