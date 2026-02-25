from fastapi import APIRouter, Depends, HTTPException
from models import Claim, ClaimCreate, User
from auth import get_current_active_user
from database import get_database
from datetime import datetime, timezone
from typing import List, Optional
import uuid

router = APIRouter(prefix="/claims", tags=["claims"])

@router.post("/", response_model=Claim)
async def create_claim(
    claim_data: ClaimCreate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    claim_dict = claim_data.model_dump()
    claim_dict["id"] = str(uuid.uuid4())
    claim_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    claim_dict["filed_by"] = current_user.id
    
    await db.claims.insert_one(claim_dict)
    return Claim(**claim_dict)

@router.get("/", response_model=List[Claim])
async def get_claims(
    status: Optional[str] = None,
    claim_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    query = {}
    if status:
        query["status"] = status
    if claim_type:
        query["type"] = claim_type
    
    claims = await db.claims.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return claims

@router.get("/{claim_id}", response_model=Claim)
async def get_claim(
    claim_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    claim = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return Claim(**claim)

@router.patch("/{claim_id}")
async def update_claim(
    claim_id: str,
    status: Optional[str] = None,
    resolution_notes: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    update_dict = {}
    if status:
        update_dict["status"] = status
        if status == "resolved":
            update_dict["resolved_at"] = datetime.now(timezone.utc).isoformat()
    if resolution_notes:
        update_dict["resolution_notes"] = resolution_notes
    
    result = await db.claims.update_one(
        {"id": claim_id},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    claim = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    return Claim(**claim)

@router.delete("/{claim_id}")
async def delete_claim(
    claim_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    result = await db.claims.delete_one({"id": claim_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {"message": "Claim deleted successfully"}

@router.get("/order/{order_id}")
async def get_order_claims(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    claims = await db.claims.find({"order_id": order_id}, {"_id": 0}).to_list(100)
    return claims
