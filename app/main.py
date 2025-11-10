from fastapi import FastAPI
from app.routes import matches

app = FastAPI(title="Sports Stats API 🏆")

app.include_router(matches.router, prefix="/api", tags=["Matches"])


@app.get("/")
def root():
    return {"message": "Sports Stats API is running 🏆"}
