from fastapi import APIRouter, Depends, HTTPException, Query
from models import Claim, ClaimCreate, ClaimStatus, ClaimType, User
from auth import get_current_active_user
from database import get_database
from datetime import datetime, timezone
from typing import List, Optional
import uuid

router = APIRouter(prefix="/claims", tags=["claims"])

@router.post("/", response_model=Claim)
async def create_claim(
    claim_req: ClaimCreate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Create a new claim"""
    # Get related entity details
    order_number = None
    if claim_req.order_id:
        order = await db.orders.find_one({"id": claim_req.order_id}, {"_id": 0})
        if order:
            order_number = order.get("order_number")
    
    claim_dict = claim_req.model_dump()
    claim_dict["id"] = str(uuid.uuid4())
    claim_dict["order_number"] = order_number
    claim_dict["claim_status"] = ClaimStatus.DRAFT
    claim_dict["status_history"] = []
    claim_dict["filed_by"] = current_user.email
    claim_dict["filed_date"] = datetime.now(timezone.utc).isoformat()
    claim_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    claim_dict["correspondence"] = []
    claim_dict["supporting_documents"] = []
    claim_dict["evidence_images"] = []
    
    await db.claims.insert_one(claim_dict)
    
    return Claim(**claim_dict)

@router.get("/", response_model=List[Claim])
async def list_claims(
    status: Optional[str] = None,
    claim_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(100, le=500),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """List all claims with optional filters"""
    query = {}
    if status:
        query["claim_status"] = status
    if claim_type:
        query["claim_type"] = claim_type
    if search:
        query["$or"] = [
            {"order_number": {"$regex": search, "$options": "i"}},
            {"claim_against": {"$regex": search, "$options": "i"}},
            {"claim_reference": {"$regex": search, "$options": "i"}}
        ]
    
    claims = await db.claims.find(query, {"_id": 0}).sort("filed_date", -1).limit(limit).to_list(limit)
    return [Claim(**c) for c in claims]

@router.get("/{claim_id}", response_model=Claim)
async def get_claim(
    claim_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get claim by ID"""
    claim = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return Claim(**claim)

@router.patch("/{claim_id}/status")
async def update_claim_status(
    claim_id: str,
    new_status: ClaimStatus,
    approved_amount: Optional[float] = None,
    rejection_reason: Optional[str] = None,
    appeal_notes: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Update claim status"""
    claim = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    current_status = claim.get("claim_status")
    
    # Build update data
    update_data = {
        "claim_status": new_status,
        "previous_status": current_status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if new_status == ClaimStatus.FILED:
        update_data["filed_date"] = datetime.now(timezone.utc).isoformat()
    
    elif new_status == ClaimStatus.APPROVED:
        update_data["resolution_date"] = datetime.now(timezone.utc).isoformat()
        if approved_amount:
            update_data["approved_amount"] = approved_amount
    
    elif new_status == ClaimStatus.PARTIALLY_APPROVED:
        update_data["resolution_date"] = datetime.now(timezone.utc).isoformat()
        if approved_amount:
            update_data["approved_amount"] = approved_amount
    
    elif new_status == ClaimStatus.REJECTED:
        update_data["resolution_date"] = datetime.now(timezone.utc).isoformat()
        if rejection_reason:
            update_data["rejection_reason"] = rejection_reason
    
    elif new_status == ClaimStatus.APPEALED:
        if appeal_notes:
            update_data["appeal_notes"] = appeal_notes
    
    elif new_status == ClaimStatus.CLOSED:
        update_data["resolution_date"] = datetime.now(timezone.utc).isoformat()
    
    if notes:
        update_data["internal_notes"] = notes
    
    # Record history
    history_entry = {
        "from_status": current_status,
        "to_status": str(new_status),
        "changed_at": datetime.now(timezone.utc).isoformat(),
        "changed_by": current_user.email,
        "notes": notes or ""
    }
    
    await db.claims.update_one(
        {"id": claim_id},
        {"$set": update_data, "$push": {"status_history": history_entry}}
    )
    
    updated_claim = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    return Claim(**updated_claim)

@router.patch("/{claim_id}/documents")
async def add_claim_documents(
    claim_id: str,
    document_urls: List[str],
    document_type: str = "supporting",  # supporting or evidence
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Add documents/images to claim"""
    field = "supporting_documents" if document_type == "supporting" else "evidence_images"
    
    result = await db.claims.update_one(
        {"id": claim_id},
        {"$push": {field: {"$each": document_urls}}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    return {"message": f"{len(document_urls)} {document_type} documents added successfully"}

@router.post("/{claim_id}/correspondence")
async def add_correspondence(
    claim_id: str,
    message: str,
    message_type: str = "note",  # note, email, call
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Add correspondence/communication entry to claim"""
    correspondence_entry = {
        "type": message_type,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "by": current_user.email
    }
    
    result = await db.claims.update_one(
        {"id": claim_id},
        {"$push": {"correspondence": correspondence_entry}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    return {"message": "Correspondence added successfully"}

@router.get("/analytics/by-type")
async def get_claims_by_type(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get claims analytics by type"""
    pipeline = [
        {
            "$group": {
                "_id": "$claim_type",
                "count": {"$sum": 1},
                "total_claimed": {"$sum": "$claim_amount"},
                "total_approved": {"$sum": {"$ifNull": ["$approved_amount", 0]}}
            }
        },
        {"$sort": {"count": -1}}
    ]
    
    results = await db.claims.aggregate(pipeline).to_list(100)
    
    formatted = []
    for r in results:
        formatted.append({
            "claim_type": r["_id"],
            "count": r["count"],
            "total_claimed": r["total_claimed"],
            "total_approved": r["total_approved"],
            "approval_rate": round((r["total_approved"] / r["total_claimed"] * 100), 2) if r["total_claimed"] > 0 else 0
        })
    
    return {"analytics": formatted}

@router.get("/analytics/by-status")
async def get_claims_by_status(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get claims analytics by status"""
    pipeline = [
        {
            "$group": {
                "_id": "$claim_status",
                "count": {"$sum": 1},
                "total_amount": {"$sum": "$claim_amount"}
            }
        },
        {"$sort": {"count": -1}}
    ]
    
    results = await db.claims.aggregate(pipeline).to_list(100)
    
    formatted = []
    for r in results:
        formatted.append({
            "status": r["_id"],
            "count": r["count"],
            "total_amount": r["total_amount"]
        })
    
    return {"analytics": formatted}
