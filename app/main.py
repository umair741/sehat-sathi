from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router

app = FastAPI(title="Sehat Sathi", description="AI Health Assistant for Pakistan")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(health_router)


@app.get("/")
def root():
    return {"status": "Sehat Sathi API running", "docs": "/docs"}
