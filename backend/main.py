from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(
    title="SmartCart API",
    description="AI-powered grocery price intelligence platform",
    version="1.0.0"
)

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