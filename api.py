# api.py

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from skills.gathere_skill import run_gathere_skill

app = FastAPI(title="Gathere Skill API")


class Participant(BaseModel):
    name: str
    address: str


class RecommendRequest(BaseModel):
    participants: List[Participant]
    keywords: str = "餐厅"
    city: str = "苏州"
    mode: str = "transit"
    top_k: int = 3
    strategy: str = "balanced"


@app.post("/recommend")
def recommend(req: RecommendRequest):
    return run_gathere_skill(
        participants=[p.model_dump() for p in req.participants],
        keywords=req.keywords,
        city=req.city,
        mode=req.mode,
        top_k=req.top_k,
        strategy=req.strategy,
    )