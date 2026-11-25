
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, upload

app = FastAPI(
    title="DataLens AI API",
    description="AI-powered data analytics and dashboard copilot",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(upload.router, prefix="/api", tags=["Dataset Upload"])


@app.get("/")
def root():
    return {"message": "Welcome to DataLens AI"}
