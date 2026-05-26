"""Beverage Recipe & Knowledge Base API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import combinations, ingredients, recipes

app = FastAPI(
    title="Beverage Recipe & Knowledge Base",
    description="Personal recipe and ingredient knowledge base for health-and-wellness beverages",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingredients.router)
app.include_router(recipes.router)
app.include_router(combinations.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
