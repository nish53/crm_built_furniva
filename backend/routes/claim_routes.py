from fastapi import APIRouter, Depends, HTTPException
from models import Claim, ClaimCreate, ClaimStatus, User
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
    # Validate that the order exists (check by order_number, not id)
    if claim_data.order_id:
        order = await db.orders.find_one({"order_number": claim_data.order_id}, {"_id": 0})
        if not order:
            raise HTTPException(
                status_code=404, 
                detail=f"Order Number '{claim_data.order_id}' does not exist. Please verify the order number and try again."
            )
    
    claim_dict = claim_data.model_dump()
    claim_dict["id"] = str(uuid.uuid4())
    claim_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    claim_dict["filed_by"] = current_user.email
    claim_dict["status_history"] = [{
        "status": claim_data.status or "filed",
        "changed_at": datetime.now(timezone.utc).isoformat(),
        "changed_by": current_user.email
    }]
    claim_dict["documents"] = []
    claim_dict["evidence_images"] = []
    claim_dict["correspondence"] = []
    
    await db.claims.insert_one(claim_dict)
    return Claim(**claim_dict)

@router.get("/", response_model=List[Claim])
async def get_claims(
    status: Optional[str] = None,
    claim_type: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    query = {}
    if status:
        query["status"] = status
    if claim_type:
        query["type"] = claim_type
    if search:
        query["$or"] = [
            {"description": {"$regex": search, "$options": "i"}},
            {"reference_number": {"$regex": search, "$options": "i"}},
            {"order_id": {"$regex": search, "$options": "i"}}
        ]
    
    claims = await db.claims.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return claims

@router.get("/analytics/by-type")
async def get_claims_analytics_by_type(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get claims analytics grouped by type"""
    pipeline = [
        {
            "$group": {
                "_id": "$type",
                "count": {"$sum": 1},
                "total_amount": {"$sum": {"$ifNull": ["$amount", 0]}},
                "approved_amount": {"$sum": {"$ifNull": ["$approved_amount", 0]}}
            }
        },
        {"$sort": {"count": -1}}
    ]
    results = await db.claims.aggregate(pipeline).to_list(100)
    return {"analytics": results}

@router.get("/analytics/by-status")
async def get_claims_analytics_by_status(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get claims analytics grouped by status"""
    pipeline = [
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "total_amount": {"$sum": {"$ifNull": ["$amount", 0]}}
            }
        },
        {"$sort": {"count": -1}}
    ]
    results = await db.claims.aggregate(pipeline).to_list(100)
    return {"analytics": results}

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

@router.patch("/{claim_id}/status")
async def update_claim_status(
    claim_id: str,
    status: str,
    approved_amount: Optional[float] = None,
    rejection_reason: Optional[str] = None,
    resolution_notes: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Update claim status with approval/rejection details"""
    claim = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    update_dict = {
        "status": status,
        "reviewed_by": current_user.email,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if status in ["approved", "partially_approved"]:
        if approved_amount is not None:
            update_dict["approved_amount"] = approved_amount
    
    if status == "rejected":
        if rejection_reason:
            update_dict["rejection_reason"] = rejection_reason
    
    if status == "closed":
        update_dict["resolved_at"] = datetime.now(timezone.utc).isoformat()
        if resolution_notes:
            update_dict["resolution_notes"] = resolution_notes
    
    # Add to status history
    history_entry = {
        "status": status,
        "changed_at": datetime.now(timezone.utc).isoformat(),
        "changed_by": current_user.email,
        "notes": resolution_notes or rejection_reason
    }
    
    await db.claims.update_one(
        {"id": claim_id},
        {"$set": update_dict, "$push": {"status_history": history_entry}}
    )
    
    updated = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    return Claim(**updated)

@router.patch("/{claim_id}/documents")
async def add_claim_documents(
    claim_id: str,
    documents: List[dict],
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Add supporting documents or evidence to a claim"""
    claim = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Add metadata to each document
    for doc in documents:
        doc["uploaded_at"] = datetime.now(timezone.utc).isoformat()
        doc["uploaded_by"] = current_user.email
    
    await db.claims.update_one(
        {"id": claim_id},
        {
            "$push": {"documents": {"$each": documents}},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    return {"message": f"{len(documents)} documents added successfully"}

@router.post("/{claim_id}/correspondence")
async def add_claim_correspondence(
    claim_id: str,
    message: str,
    to_party: Optional[str] = None,
    comm_type: Optional[str] = "note",
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Add communication entry to claim"""
    claim = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    entry = {
        "id": str(uuid.uuid4()),
        "date": datetime.now(timezone.utc).isoformat(),
        "from": current_user.email,
        "to": to_party,
        "message": message,
        "type": comm_type  # note, email, call, platform_message
    }
    
    await db.claims.update_one(
        {"id": claim_id},
        {
            "$push": {"correspondence": entry},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    return {"message": "Correspondence added successfully", "entry": entry}

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
