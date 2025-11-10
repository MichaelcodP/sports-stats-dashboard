from fastapi import FastAPI

app = FastAPI(
    title="Sports Stats Dashboard",
    description="API for soccer match stats and LLM analysis",
    version="1.0.0",
)

@app.get("/")
def root():
    return {"message": "Sports Stats API is running 🏆"}