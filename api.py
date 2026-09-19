# api.py

import config
from config import DEFAULT_CITY
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from typing import List, Literal, Optional

from skills.gathere_skill import run_gathere_skill

app = FastAPI(title="Gathere Skill API")


class Participant(BaseModel):
    name: str
    address: str
    # Per-participant travel mode; falls back to the request-level mode.
    mode: Optional[Literal["driving", "walking", "transit"]] = None


class RecommendRequest(BaseModel):
    participants: List[Participant]
    keywords: str = "餐厅"
    city: str = DEFAULT_CITY
    mode: Literal["driving", "walking", "transit"] = "transit"
    top_k: int = Field(default=3, ge=1, le=10)
    strategy: Literal["balanced", "fair", "fast"] = "balanced"
    max_cost: Optional[float] = Field(default=None, gt=0)


def require_api_key(x_api_key: Optional[str] = Header(default=None)):
    """Reject requests when GATHERE_API_KEY is configured in .env."""
    if config.GATHERE_API_KEY and x_api_key != config.GATHERE_API_KEY:
        raise HTTPException(status_code=401, detail="invalid or missing X-API-Key")


@app.post("/recommend", dependencies=[Depends(require_api_key)])
def recommend(req: RecommendRequest):
    return run_gathere_skill(
        participants=[p.model_dump(exclude_none=True) for p in req.participants],
        keywords=req.keywords,
        city=req.city,
        mode=req.mode,
        top_k=req.top_k,
        strategy=req.strategy,
        max_cost=req.max_cost,
    )
