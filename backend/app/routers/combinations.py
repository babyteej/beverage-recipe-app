"""Combination suggestion API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from supabase import Client

from app.db.supabase_client import get_supabase_client
from app.models.api import CombinationSuggestRequest, CombinationSuggestResponse
from app.services.combination_service import suggest_combinations

router = APIRouter(prefix="/combinations", tags=["combinations"])


def get_db() -> Client:
    return get_supabase_client()


@router.post("/suggest", response_model=CombinationSuggestResponse)
def suggest(body: CombinationSuggestRequest, db: Annotated[Client, Depends(get_db)]):
    return suggest_combinations(db, body)
