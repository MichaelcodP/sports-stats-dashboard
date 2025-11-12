from fastapi import FastAPI
from app.routes import analysis, matches

app = FastAPI(title="Sports Stats API 🏆")

app.include_router(matches.router, prefix="/api", tags=["Matches"])
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])


@app.get("/")
def root():
    return {"message": "Sports Stats API is running 🏆"}
