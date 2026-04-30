from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import upload

app = FastAPI(
    title="Data Analyst API",
    description="API for automated data analysis and insights",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api", tags=["upload"])


@app.get("/")
async def root():
    return {
        "message": "Data Analyst API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/api/upload",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
