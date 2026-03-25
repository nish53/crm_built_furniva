from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from models import ReturnRequest, ReturnRequestCreate, ReturnStatus, ReturnType, User
from auth import get_current_active_user
from database import get_database
from datetime import datetime, timezone
from typing import List, Optional
import uuid

router = APIRouter(prefix="/return-requests", tags=["return-requests"])

def classify_return_category(return_reason: str, status: str, delivery_date: str = None) -> str:
    """
    Classify return into categories: pfc, resolved, refunded, or fraud
    Never returns 'unknown'
    """
    reason_lower = (return_reason or "").lower()
    
    # Check for fraud indicators first (highest priority)
    if "fraud" in reason_lower or "cancelled and delivered" in reason_lower:
        return "fraud"
    
    # Check for Pre-Fulfillment Cancel (PFC)
    # PFC: Order was cancelled before delivery (no delivery_date and cancelled/returned status)
    if "pre fulfillment" in reason_lower or "pfc" in reason_lower:
        return "pfc"
    
    # If cancelled without delivery, it's likely PFC
    if status in ["cancelled", "returned"] and not delivery_date:
        if "fraud" not in reason_lower:  # Exclude fraud cases
            return "pfc"
    
    # Resolved: Issues that were resolved (damage fixed, replacement provided)
    resolved_keywords = ["resolved", "replaced", "fixed", "repaired", "hardware", "quality"]
    if any(kw in reason_lower for kw in resolved_keywords):
        return "resolved"
    
    # Default to refunded for all other return cases
    return "refunded"

# Workflow transition map - defines allowed next statuses for each status
WORKFLOW_TRANSITIONS = {
    "requested": ["feedback_check", "authorized", "rejected", "cancelled"],
    "feedback_check": ["claim_filed", "authorized", "rejected", "cancelled"],
    "claim_filed": ["authorized", "rejected", "cancelled"],
    "authorized": ["return_initiated", "cancelled"],
    "return_initiated": ["in_transit", "cancelled"],
    "in_transit": ["warehouse_received"],
    "warehouse_received": ["qc_inspection"],
    "qc_inspection": ["claim_filing", "refund_processed", "closed"],
    "claim_filing": ["claim_status"],
    "claim_status": ["refund_processed", "closed"],
    "refund_processed": ["closed"],
    "closed": [],
    "rejected": [],
    "cancelled": [],
    # Legacy transitions for backward compatibility
    "approved": ["pickup_scheduled", "return_initiated", "cancelled"],
    "pickup_scheduled": ["in_transit", "cancelled"],
    "received": ["inspected", "qc_inspection"],
    "inspected": ["refunded", "refund_processed", "replaced", "closed"],
    "refunded": ["closed"],
    "replaced": ["closed"],
}

# Stage-specific field mappings
STAGE_DATE_FIELDS = {
    "feedback_check": "feedback_check_date",
    "claim_filed": "claim_filed_date",
    "authorized": "authorized_date",
    "return_initiated": "return_initiated_date",
    "in_transit": None,  # Uses return_tracking_number
    "warehouse_received": "warehouse_received_date",
    "qc_inspection": "qc_inspection_date",
    "claim_filing": "claim_filing_date",
    "claim_status": "claim_status_date",
    "refund_processed": "refund_processed_date",
    "closed": "closed_date",
    # Legacy
    "approved": "approved_date",
    "pickup_scheduled": "pickup_date",
    "received": "received_date",
    "inspected": "inspection_date",
    "refunded": "refund_date",
}

@router.post("/", response_model=ReturnRequest)
async def create_return_request(
    return_req: ReturnRequestCreate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Create a new return request"""
    # Get order details
    order = await db.orders.find_one({"id": return_req.order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Classify the return category
    category = classify_return_category(
        return_reason=return_req.return_reason,
        status=order.get("status", ""),
        delivery_date=order.get("delivery_date")
    )
    
    # Create return request
    return_dict = return_req.model_dump()
    return_dict["id"] = str(uuid.uuid4())
    return_dict["order_number"] = order["order_number"]
    return_dict["customer_id"] = order["customer_id"]
    return_dict["customer_name"] = order["customer_name"]
    return_dict["phone"] = order["phone"]
    return_dict["return_status"] = ReturnStatus.REQUESTED
    return_dict["requested_date"] = datetime.now(timezone.utc).isoformat()
    return_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    return_dict["category"] = category  # Add classified category
    return_dict["status_history"] = [{
        "from_status": None,
        "to_status": ReturnStatus.REQUESTED,
        "changed_at": datetime.now(timezone.utc).isoformat(),
        "changed_by": current_user.email
    }]
    
    await db.return_requests.insert_one(return_dict)
    
    # Update order - sync return_reason to cancellation_reason as well
    await db.orders.update_one(
        {"id": return_req.order_id},
        {"$set": {
            "return_requested": True,
            "return_reason": return_req.return_reason,
            "cancellation_reason": return_req.return_reason,  # Sync to cancellation_reason
            "return_date": datetime.now(timezone.utc).isoformat(),
            "loss_category": category  # Also set loss category on order
        }}
    )
    
    return ReturnRequest(**return_dict)

@router.get("/", response_model=List[ReturnRequest])
async def get_return_requests(
    status: Optional[ReturnStatus] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get all return requests"""
    query = {}
    
    if status:
        query["return_status"] = status
    
    if start_date:
        query["requested_date"] = {"$gte": start_date}
    if end_date:
        if "requested_date" not in query:
            query["requested_date"] = {}
        query["requested_date"]["$lte"] = end_date
    
    returns = await db.return_requests.find(query, {"_id": 0}).sort("requested_date", -1).skip(skip).limit(limit).to_list(limit)
    return returns

@router.get("/{return_id}", response_model=ReturnRequest)
async def get_return_request(
    return_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get return request by ID"""
    return_req = await db.return_requests.find_one({"id": return_id}, {"_id": 0})
    if not return_req:
        raise HTTPException(status_code=404, detail="Return request not found")
    return ReturnRequest(**return_req)

@router.patch("/{return_id}/status")
async def update_return_status(
    return_id: str,
    status: ReturnStatus,
    pickup_date: Optional[str] = None,
    tracking_number: Optional[str] = None,
    courier_partner: Optional[str] = None,
    notes: Optional[str] = None,
    refund_amount: Optional[float] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Update return request status with mandatory field validation"""
    return_req = await db.return_requests.find_one({"id": return_id}, {"_id": 0})
    if not return_req:
        raise HTTPException(status_code=404, detail="Return request not found")

    # Mandatory field validation
    if status == ReturnStatus.PICKUP_SCHEDULED and not pickup_date:
        raise HTTPException(status_code=400, detail="Pickup date is mandatory for Pickup Scheduled status")
    if status == ReturnStatus.IN_TRANSIT and not tracking_number:
        raise HTTPException(status_code=400, detail="Tracking number is mandatory for In Transit status")

    # Record status history
    history_entry = {
        "from_status": return_req.get("return_status"),
        "to_status": status,
        "changed_at": datetime.now(timezone.utc).isoformat(),
        "changed_by": current_user.email
    }

    update_data = {
        "return_status": status,
        "previous_status": return_req.get("return_status"),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    # Update date/tracking fields based on status
    if status == ReturnStatus.APPROVED:
        update_data["approved_date"] = datetime.now(timezone.utc).isoformat()
    elif status == ReturnStatus.PICKUP_SCHEDULED:
        update_data["pickup_date"] = pickup_date
    elif status == ReturnStatus.IN_TRANSIT:
        update_data["return_tracking_number"] = tracking_number
        if courier_partner:
            update_data["courier_partner"] = courier_partner
    elif status == ReturnStatus.RECEIVED:
        update_data["received_date"] = datetime.now(timezone.utc).isoformat()
    elif status == ReturnStatus.INSPECTED:
        update_data["inspection_date"] = datetime.now(timezone.utc).isoformat()
    elif status == ReturnStatus.REFUNDED:
        update_data["refund_date"] = datetime.now(timezone.utc).isoformat()
        if refund_amount:
            update_data["refund_amount"] = refund_amount

    if notes:
        update_data["qc_notes"] = notes

    await db.return_requests.update_one(
        {"id": return_id},
        {"$set": update_data, "$push": {"status_history": history_entry}}
    )

    # Update order status
    await db.orders.update_one(
        {"id": return_req["order_id"]},
        {"$set": {"return_status": status}}
    )

    updated_return = await db.return_requests.find_one({"id": return_id}, {"_id": 0})
    return ReturnRequest(**updated_return)


@router.patch("/{return_id}/undo")
async def undo_return_status(
    return_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Undo the last status change on a return request"""
    return_req = await db.return_requests.find_one({"id": return_id}, {"_id": 0})
    if not return_req:
        raise HTTPException(status_code=404, detail="Return request not found")

    previous = return_req.get("previous_status")
    if not previous:
        raise HTTPException(status_code=400, detail="No previous status to revert to")

    # Record undo in history
    history_entry = {
        "from_status": return_req.get("return_status"),
        "to_status": previous,
        "changed_at": datetime.now(timezone.utc).isoformat(),
        "changed_by": current_user.email,
        "is_undo": True
    }

    update_data = {
        "return_status": previous,
        "previous_status": None,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    await db.return_requests.update_one(
        {"id": return_id},
        {"$set": update_data, "$push": {"status_history": history_entry}}
    )

    # Also revert order status
    await db.orders.update_one(
        {"id": return_req["order_id"]},
        {"$set": {"return_status": previous}}
    )

    updated_return = await db.return_requests.find_one({"id": return_id}, {"_id": 0})
    return ReturnRequest(**updated_return)

@router.patch("/{return_id}/workflow/advance")
async def advance_return_workflow(
    return_id: str,
    next_status: str,
    # Stage-specific optional fields
    tracking_number: Optional[str] = None,
    courier_partner: Optional[str] = None,
    notes: Optional[str] = None,
    refund_amount: Optional[float] = None,
    pickup_date: Optional[str] = None,
    feedback_outcome: Optional[str] = None,
    claim_reference: Optional[str] = None,
    claim_platform: Optional[str] = None,
    claim_amount: Optional[float] = None,
    return_method: Optional[str] = None,
    qc_result: Optional[str] = None,
    qc_damage_found: Optional[str] = None,
    claim_status_result: Optional[str] = None,
    claim_approved_amount: Optional[float] = None,
    refund_method: Optional[str] = None,
    refund_transaction_id: Optional[str] = None,
    resolution_summary: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Advance return through workflow stages with validation"""
    return_req = await db.return_requests.find_one({"id": return_id}, {"_id": 0})
    if not return_req:
        raise HTTPException(status_code=404, detail="Return request not found")
    
    current_status = return_req.get("return_status", "requested")
    
    # Validate transition is allowed
    allowed = WORKFLOW_TRANSITIONS.get(current_status, [])
    if next_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{current_status}' to '{next_status}'. Allowed: {allowed}"
        )
    
    # Validate required fields for specific stages
    if next_status == "in_transit" and not tracking_number:
        raise HTTPException(status_code=400, detail="Tracking number is required for in_transit status")
    if next_status == "pickup_scheduled" and not pickup_date:
        raise HTTPException(status_code=400, detail="Pickup date is required for pickup_scheduled status")
    
    # Build update data
    now = datetime.now(timezone.utc).isoformat()
    update_data = {
        "return_status": next_status,
        "previous_status": current_status,
        "updated_at": now
    }
    
    # Set stage-specific date
    date_field = STAGE_DATE_FIELDS.get(next_status)
    if date_field:
        update_data[date_field] = now
    
    # Set stage-specific fields
    if next_status == "feedback_check":
        if notes:
            update_data["feedback_check_notes"] = notes
        if feedback_outcome:
            update_data["feedback_check_outcome"] = feedback_outcome
    
    elif next_status == "claim_filed":
        if claim_reference:
            update_data["claim_reference"] = claim_reference
        if claim_platform:
            update_data["claim_platform"] = claim_platform
        if claim_amount:
            update_data["claim_amount"] = claim_amount
    
    elif next_status == "authorized":
        update_data["authorized_by"] = current_user.email
        if notes:
            update_data["authorization_notes"] = notes
    
    elif next_status == "return_initiated":
        if return_method:
            update_data["return_method"] = return_method
    
    elif next_status == "in_transit":
        update_data["return_tracking_number"] = tracking_number
        if courier_partner:
            update_data["courier_partner"] = courier_partner
    
    elif next_status == "warehouse_received":
        update_data["warehouse_received_by"] = current_user.email
        if notes:
            update_data["warehouse_notes"] = notes
    
    elif next_status == "qc_inspection":
        update_data["qc_inspector"] = current_user.email
        if qc_result:
            update_data["qc_result"] = qc_result
        if qc_damage_found:
            update_data["qc_damage_found"] = qc_damage_found
        if notes:
            update_data["qc_notes"] = notes
    
    elif next_status == "claim_filing":
        if claim_reference:
            update_data["claim_filing_reference"] = claim_reference
        if claim_platform:
            update_data["claim_filing_platform"] = claim_platform
        if claim_amount:
            update_data["claim_filing_amount"] = claim_amount
        if notes:
            update_data["claim_filing_notes"] = notes
    
    elif next_status == "claim_status":
        if claim_status_result:
            update_data["claim_status_result"] = claim_status_result
        if claim_approved_amount:
            update_data["claim_approved_amount"] = claim_approved_amount
        if notes:
            update_data["claim_status_notes"] = notes
    
    elif next_status == "refund_processed":
        if refund_amount:
            update_data["refund_processed_amount"] = refund_amount
        if refund_method:
            update_data["refund_processed_method"] = refund_method
        if refund_transaction_id:
            update_data["refund_transaction_id"] = refund_transaction_id
    
    elif next_status == "closed":
        update_data["closed_by"] = current_user.email
        if notes:
            update_data["closure_notes"] = notes
        if resolution_summary:
            update_data["resolution_summary"] = resolution_summary
    
    # Legacy status fields
    elif next_status == "pickup_scheduled":
        if pickup_date:
            update_data["pickup_date"] = pickup_date
    elif next_status == "refunded":
        if refund_amount:
            update_data["refund_amount"] = refund_amount
    
    # Generic notes
    if notes and next_status not in ["feedback_check", "authorized", "warehouse_received", "qc_inspection", "claim_filing", "claim_status", "closed"]:
        update_data["qc_notes"] = notes
    
    # Record in status history
    history_entry = {
        "from_status": current_status,
        "to_status": next_status,
        "changed_at": now,
        "changed_by": current_user.email,
        "notes": notes
    }
    
    await db.return_requests.update_one(
        {"id": return_id},
        {"$set": update_data, "$push": {"status_history": history_entry}}
    )
    
    # Update order return_status
    await db.orders.update_one(
        {"id": return_req["order_id"]},
        {"$set": {"return_status": next_status}}
    )
    
    updated = await db.return_requests.find_one({"id": return_id}, {"_id": 0})
    return updated

@router.get("/{return_id}/workflow-stages")
async def get_workflow_stages(
    return_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get allowed next workflow stages for a return request"""
    return_req = await db.return_requests.find_one({"id": return_id}, {"_id": 0})
    if not return_req:
        raise HTTPException(status_code=404, detail="Return request not found")
    
    current_status = return_req.get("return_status", "requested")
    allowed = WORKFLOW_TRANSITIONS.get(current_status, [])
    
    return {
        "current_status": current_status,
        "allowed_transitions": allowed,
        "is_terminal": len(allowed) == 0
    }

@router.patch("/{return_id}/qc-images")
async def add_qc_images(
    return_id: str,
    image_urls: List[str],
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Add QC inspection images to return request"""
    result = await db.return_requests.update_one(
        {"id": return_id},
        {
            "$push": {"qc_images": {"$each": image_urls}},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Return request not found")
    
    return {"message": f"{len(image_urls)} QC images added successfully"}

@router.post("/{return_id}/add-image")
async def add_damage_image(
    return_id: str,
    image_url: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Add damage image to return request"""
    result = await db.return_requests.update_one(
        {"id": return_id},
        {"$push": {"damage_images": image_url}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Return request not found")
    
    return {"message": "Image added successfully"}

@router.get("/analytics/reasons")
async def get_return_reasons_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get analytics on return reasons"""
    pipeline = []
    
    match_stage = {}
    if start_date:
        match_stage["requested_date"] = {"$gte": start_date}
    if end_date:
        if "requested_date" not in match_stage:
            match_stage["requested_date"] = {}
        match_stage["requested_date"]["$lte"] = end_date
    
    if match_stage:
        pipeline.append({"$match": match_stage})
    
    pipeline.extend([
        {
            "$group": {
                "_id": "$return_reason",
                "count": {"$sum": 1},
                "total_refund": {"$sum": {"$ifNull": ["$refund_amount", 0]}}
            }
        },
        {"$sort": {"count": -1}}
    ])
    
    results = await db.return_requests.aggregate(pipeline).to_list(100)
    return {"analytics": results}

@router.get("/analytics/by-product")
async def get_returns_by_product(
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get products with highest return rates"""
    # Get all returns with order details
    returns = await db.return_requests.find({}, {"_id": 0, "order_id": 1}).to_list(1000)
    order_ids = [r["order_id"] for r in returns]
    
    # Get orders
    orders = await db.orders.find({"id": {"$in": order_ids}}, {"_id": 0, "master_sku": 1, "sku": 1, "product_name": 1}).to_list(1000)
    
    # Count by SKU
    sku_counts = {}
    for order in orders:
        sku = order.get("master_sku") or order.get("sku")
        if sku:
            if sku not in sku_counts:
                sku_counts[sku] = {
                    "sku": sku,
                    "product_name": order.get("product_name", "Unknown"),
                    "return_count": 0
                }
            sku_counts[sku]["return_count"] += 1
    
    # Sort and return top
    sorted_products = sorted(sku_counts.values(), key=lambda x: x["return_count"], reverse=True)[:limit]
    return {"products": sorted_products}
