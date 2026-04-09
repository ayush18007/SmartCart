from fastapi import FastAPI
from dotenv import load_dotenv
from database import test_connection
import os

load_dotenv()

app = FastAPI(
    title="SmartCart API",
    description="AI-powered grocery price intelligence platform",
    version="1.0.0"
)

@app.on_event("startup")
async def startup():
    test_connection()

@app.get("/")
def home():
    return {
        "message": "Welcome to SmartCart API",
        "status": "running"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": os.getenv("DATABASE_URL") is not None
    }