from fastapi import APIRouter, Depends, HTTPException
from models import ReplacementRequest, ReplacementRequestCreate, ReplacementStatus, ReplacementReason, User
from auth import get_current_active_user
from database import get_database
from datetime import datetime, timezone
from typing import List, Optional
import uuid

router = APIRouter(prefix="/replacement-requests", tags=["replacement-requests"])

@router.post("/", response_model=ReplacementRequest)
async def create_replacement_request(
    replacement_req: ReplacementRequestCreate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Create a new replacement request with full/partial replacement support.
    - Reasons: damaged, quality, wrong_product_sent, customer_change_of_mind
    - For damaged/quality: Can choose full or partial replacement
    - For wrong_product_sent/customer_change_of_mind: Only full replacement
    """
    # Validate images provided
    if not replacement_req.damage_images or len(replacement_req.damage_images) == 0:
        raise HTTPException(status_code=400, detail="At least one damage image is required")
    
    # Validate replacement_type
    if not replacement_req.replacement_type:
        raise HTTPException(status_code=400, detail="replacement_type is required (full_replacement or partial_replacement)")
    
    # Validate replacement_type based on reason
    if replacement_req.replacement_reason in ["wrong_product_sent", "customer_change_of_mind"]:
        if replacement_req.replacement_type != "full_replacement":
            raise HTTPException(
                status_code=400,
                detail=f"Only full_replacement is allowed for reason '{replacement_req.replacement_reason}'"
            )
    
    # Validate difference_amount for customer_change_of_mind
    if replacement_req.replacement_reason == "customer_change_of_mind":
        if replacement_req.difference_amount is None:
            raise HTTPException(
                status_code=400,
                detail="difference_amount is required for customer_change_of_mind (can be 0 if no upsell)"
            )
    
    # Get order details
    order = await db.orders.find_one({"id": replacement_req.order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Create replacement request
    replacement_dict = replacement_req.model_dump()
    replacement_dict["id"] = str(uuid.uuid4())
    replacement_dict["order_number"] = order["order_number"]
    replacement_dict["customer_id"] = order.get("customer_id", "")
    replacement_dict["customer_name"] = order["customer_name"]
    replacement_dict["phone"] = order["phone"]
    replacement_dict["replacement_status"] = ReplacementStatus.REQUESTED
    replacement_dict["requested_date"] = datetime.now(timezone.utc).isoformat()
    replacement_dict["created_by"] = current_user.email
    replacement_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    replacement_dict["pickup_not_required"] = False
    replacement_dict["delivery_confirmed"] = False
    replacement_dict["status_history"] = [{
        "status": ReplacementStatus.REQUESTED,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "changed_by": current_user.email,
        "replacement_type": replacement_req.replacement_type,
        "notes": replacement_req.notes
    }]
    
    await db.replacement_requests.insert_one(replacement_dict)
    
    # Update order to mark replacement requested
    await db.orders.update_one(
        {"id": replacement_req.order_id},
        {"$set": {
            "replacement_requested": True,
            "replacement_reason": replacement_req.replacement_reason,
            "replacement_type": replacement_req.replacement_type,
            "replacement_request_date": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return ReplacementRequest(**replacement_dict)

@router.get("/", response_model=List[ReplacementRequest])
async def get_replacement_requests(
    status: Optional[ReplacementStatus] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get all replacement requests with optional status filter"""
    query = {}
    if status:
        query["replacement_status"] = status
    
    replacements = await db.replacement_requests.find(query, {"_id": 0}).sort("requested_date", -1).to_list(None)
    return replacements

@router.get("/{replacement_id}", response_model=ReplacementRequest)
async def get_replacement_request(
    replacement_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get a specific replacement request"""
    replacement = await db.replacement_requests.find_one({"id": replacement_id}, {"_id": 0})
    if not replacement:
        raise HTTPException(status_code=404, detail="Replacement request not found")
    return ReplacementRequest(**replacement)

@router.patch("/{replacement_id}/status")
async def update_replacement_status(
    replacement_id: str,
    new_status: ReplacementStatus,
    tracking_number: Optional[str] = None,
    issue_resolved: Optional[bool] = None,
    resolution_notes: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Update replacement request status and tracking info"""
    replacement = await db.replacement_requests.find_one({"id": replacement_id}, {"_id": 0})
    if not replacement:
        raise HTTPException(status_code=404, detail="Replacement request not found")
    
    update_data = {
        "replacement_status": new_status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Update specific fields based on status
    if new_status == ReplacementStatus.PRIORITY_REVIEW:
        update_data["priority_review_date"] = datetime.now(timezone.utc).isoformat()
    
    elif new_status == ReplacementStatus.SHIP_REPLACEMENT:
        update_data["ship_date"] = datetime.now(timezone.utc).isoformat()
    
    elif new_status == ReplacementStatus.TRACKING_ADDED:
        if not tracking_number:
            raise HTTPException(status_code=400, detail="Tracking number required for this status")
        update_data["tracking_number"] = tracking_number
        update_data["tracking_added_date"] = datetime.now(timezone.utc).isoformat()
    
    elif new_status == ReplacementStatus.DELIVERED:
        update_data["delivered_date"] = datetime.now(timezone.utc).isoformat()
    
    elif new_status in [ReplacementStatus.RESOLVED, ReplacementStatus.NOT_RESOLVED]:
        update_data["resolved_date"] = datetime.now(timezone.utc).isoformat()
        if issue_resolved is not None:
            update_data["issue_resolved"] = issue_resolved
        if resolution_notes:
            update_data["resolution_notes"] = resolution_notes
    
    # Add to status history
    status_history = replacement.get("status_history", [])
    status_history.append({
        "status": new_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "changed_by": current_user.email,
        "tracking_number": tracking_number,
        "notes": resolution_notes
    })
    update_data["status_history"] = status_history
    
    await db.replacement_requests.update_one({"id": replacement_id}, {"$set": update_data})
    
    return {"message": "Replacement status updated successfully", "new_status": new_status}

@router.patch("/{replacement_id}/advance")
async def advance_replacement_workflow(
    replacement_id: str,
    next_status: str,
    # Common fields
    notes: Optional[str] = None,
    # Pickup phase fields
    pickup_date: Optional[str] = None,
    pickup_tracking_id: Optional[str] = None,
    pickup_courier: Optional[str] = None,
    pickup_not_required: Optional[bool] = None,
    # Warehouse phase fields
    warehouse_received_date: Optional[str] = None,
    received_condition: Optional[str] = None,  # "mint" or "damaged"
    condition_notes: Optional[str] = None,
    # New shipment phase fields (full replacement)
    new_tracking_id: Optional[str] = None,
    new_courier: Optional[str] = None,
    items_sent_description: Optional[str] = None,
    # Parts shipment fields (partial replacement)
    parts_description: Optional[str] = None,
    parts_tracking_id: Optional[str] = None,
    parts_courier: Optional[str] = None,
    # Delivery confirmation
    delivered_date: Optional[str] = None,
    delivery_confirmed: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Advance replacement through workflow with full/partial support.
    Flow: requested → approved → pickup_scheduled/pickup_not_required → 
          warehouse_received → new_shipment_dispatched/parts_shipped → delivered → resolved
    """
    replacement = await db.replacement_requests.find_one({"id": replacement_id}, {"_id": 0})
    if not replacement:
        raise HTTPException(status_code=404, detail="Replacement request not found")
    
    current_status = replacement.get("replacement_status", "requested")
    replacement_type = replacement.get("replacement_type", "full_replacement")
    
    # Define allowed transitions (simplified)
    REPLACEMENT_TRANSITIONS = {
        "requested": ["approved", "rejected"],
        "approved": ["pickup_scheduled", "pickup_not_required"],
        "pickup_scheduled": ["pickup_in_transit"],
        "pickup_in_transit": ["warehouse_received"],
        "pickup_not_required": ["new_shipment_dispatched", "parts_shipped"],  # Skip pickup
        "warehouse_received": ["new_shipment_dispatched", "parts_shipped"],
        "new_shipment_dispatched": ["delivered"],
        "parts_shipped": ["delivered"],
        "delivered": ["resolved"],
        "rejected": [],
        "resolved": []
    }
    
    allowed = REPLACEMENT_TRANSITIONS.get(current_status, [])
    if next_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{current_status}' to '{next_status}'. Allowed: {allowed}"
        )
    
    # Validate required fields
    if next_status == "pickup_scheduled" and not (pickup_date and pickup_tracking_id):
        raise HTTPException(
            status_code=400,
            detail="pickup_date and pickup_tracking_id are required"
        )
    
    if next_status == "new_shipment_dispatched" and not new_tracking_id:
        raise HTTPException(
            status_code=400,
            detail="new_tracking_id is required for new shipment"
        )
    
    if next_status == "parts_shipped" and not parts_tracking_id:
        raise HTTPException(
            status_code=400,
            detail="parts_tracking_id is required for parts shipment"
        )
    
    # Build update data
    now = datetime.now(timezone.utc).isoformat()
    update_data = {
        "replacement_status": next_status,
        "updated_at": now
    }
    
    # Set status-specific fields
    if next_status == "approved":
        update_data["approved_date"] = now
    elif next_status == "pickup_not_required":
        update_data["pickup_not_required"] = True
        # Set status directly to avoid requiring another call
        update_data["replacement_status"] = next_status
    elif next_status == "pickup_scheduled":
        update_data["pickup_date"] = pickup_date
        update_data["pickup_tracking_id"] = pickup_tracking_id
        update_data["pickup_courier"] = pickup_courier
    elif next_status == "warehouse_received":
        update_data["warehouse_received_date"] = warehouse_received_date or now
        update_data["received_condition"] = received_condition
        update_data["condition_notes"] = condition_notes
    elif next_status == "new_shipment_dispatched":
        update_data["new_tracking_id"] = new_tracking_id
        update_data["new_courier"] = new_courier
        update_data["items_sent_description"] = items_sent_description
    elif next_status == "parts_shipped":
        update_data["parts_description"] = parts_description
        update_data["parts_tracking_id"] = parts_tracking_id
        update_data["parts_courier"] = parts_courier
    elif next_status == "delivered":
        update_data["delivered_date"] = delivered_date or now
        update_data["delivery_confirmed"] = delivery_confirmed or False
    elif next_status == "resolved":
        update_data["resolved_date"] = now
        update_data["issue_resolved"] = True
    
    # Add notes
    if notes:
        update_data["notes"] = notes
    
    # Update status history
    status_history = replacement.get("status_history", [])
    status_history.append({
        "status": next_status,
        "timestamp": now,
        "changed_by": current_user.email,
        "notes": notes,
        "replacement_type": replacement_type
    })
    update_data["status_history"] = status_history
    
    # Update replacement request
    await db.replacement_requests.update_one(
        {"id": replacement_id},
        {"$set": update_data}
    )
    
    # If resolved, update order
    if next_status == "resolved":
        await db.orders.update_one(
            {"id": replacement["order_id"]},
            {"$set": {
                "replacement_status": "resolved",
                "status": "delivered"  # Mark order as delivered with resolved replacement
            }}
        )
    
    # Fetch and return updated replacement
    updated = await db.replacement_requests.find_one({"id": replacement_id}, {"_id": 0})
    return ReplacementRequest(**updated)

@router.get("/priority/pending")
async def get_priority_replacements(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get replacement requests that need priority attention"""
    query = {
        "replacement_status": {"$in": [
            ReplacementStatus.PENDING,
            ReplacementStatus.PRIORITY_REVIEW
        ]}
    }
    
    replacements = await db.replacement_requests.find(query, {"_id": 0}).sort("requested_date", 1).to_list(None)
    
    return {
        "count": len(replacements),
        "replacements": replacements
    }
