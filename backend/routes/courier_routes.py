from fastapi import APIRouter, Depends, HTTPException
from models import CourierPartner, User
from auth import get_current_active_user
from database import get_database
from typing import List, Optional
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/couriers", tags=["couriers"])

@router.post("/")
async def create_courier(
    name: str,
    base_rate: float,
    per_kg_rate: float,
    service_pincodes: Optional[List[str]] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    courier_dict = {
        "id": str(uuid.uuid4()),
        "name": name,
        "base_rate": base_rate,
        "per_kg_rate": per_kg_rate,
        "performance_score": 0.0,
        "active": True,
        "service_pincodes": service_pincodes or [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.courier_partners.insert_one(courier_dict)
    return CourierPartner(**courier_dict)

@router.get("/", response_model=List[CourierPartner])
async def get_couriers(
    active_only: bool = True,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    query = {"active": True} if active_only else {}
    couriers = await db.courier_partners.find(query, {"_id": 0}).to_list(100)
    return couriers

@router.get("/recommend/{pincode}")
async def recommend_courier(
    pincode: str,
    weight: float = 5.0,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Recommend best courier for pincode based on performance and cost"""
    couriers = await db.courier_partners.find(
        {"active": True},
        {"_id": 0}
    ).to_list(100)
    
    recommendations = []
    for courier in couriers:
        # Check if courier services this pincode
        if courier.get("service_pincodes") and pincode not in courier.get("service_pincodes", []):
            continue
        
        # Calculate cost
        cost = courier["base_rate"] + (weight * courier["per_kg_rate"])
        
        # Calculate score (performance * cost efficiency)
        score = courier["performance_score"] * (1000 / (cost + 1))
        
        recommendations.append({
            "courier": courier,
            "estimated_cost": round(cost, 2),
            "score": round(score, 2)
        })
    
    # Sort by score descending
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    
    return recommendations[:5]

@router.patch("/{courier_id}")
async def update_courier(
    courier_id: str,
    performance_score: Optional[float] = None,
    active: Optional[bool] = None,
    base_rate: Optional[float] = None,
    per_kg_rate: Optional[float] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    update_dict = {}
    if performance_score is not None:
        update_dict["performance_score"] = performance_score
    if active is not None:
        update_dict["active"] = active
    if base_rate is not None:
        update_dict["base_rate"] = base_rate
    if per_kg_rate is not None:
        update_dict["per_kg_rate"] = per_kg_rate
    
    result = await db.courier_partners.update_one(
        {"id": courier_id},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Courier not found")
    
    courier = await db.courier_partners.find_one({"id": courier_id}, {"_id": 0})
    return CourierPartner(**courier)

@router.delete("/{courier_id}")
async def delete_courier(
    courier_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    result = await db.courier_partners.delete_one({"id": courier_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Courier not found")
    return {"message": "Courier deleted successfully"}
