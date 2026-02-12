
from typing import Any, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.api import deps
from app.models.user import User

router = APIRouter()

class GenerationRequest(BaseModel):
    business_type: str
    location: str
    description: str

class RoadmapStep(BaseModel):
    id: int
    title: str
    status: str

class GenerationResponse(BaseModel):
    roadmap_id: str
    title: str
    steps: List[RoadmapStep]

@router.post("", response_model=GenerationResponse)
async def generate_roadmap(
    request: GenerationRequest,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Generate a mock roadmap based on business type.
    """
    # Mock Logic
    title = f"Mock Roadmap for {request.business_type}"
    steps = [
        {"id": 1, "title": "Market Research", "status": "PENDING"},
        {"id": 2, "title": "Location Scouting", "status": "PENDING"},
        {"id": 3, "title": "Business Registration", "status": "PENDING"},
    ]
    
    return {
        "roadmap_id": "mock-123",
        "title": title,
        "steps": steps
    }
