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
    # ONLY validate images for 'damaged' reason
    if replacement_req.replacement_reason == "damaged":
        if not replacement_req.damage_images or len(replacement_req.damage_images) == 0:
            raise HTTPException(status_code=400, detail="At least one damage image is required for damaged replacements")
        if not replacement_req.damage_description or not replacement_req.damage_description.strip():
            raise HTTPException(status_code=400, detail="Damage description is required for damaged replacements")
    
    # For non-damaged reasons, set defaults if not provided
    if replacement_req.replacement_reason != "damaged":
        if not replacement_req.damage_description:
            replacement_req.damage_description = "N/A"
        if not replacement_req.damage_images:
            replacement_req.damage_images = []
    
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
    exclude_status: Optional[str] = None,  # NEW: exclude certain statuses
    filter_type: Optional[str] = None,  # NEW: special filters for dual approval
    order_id: Optional[str] = None,  # Filter by specific order
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get all replacement requests with optional status filter and exclusion"""
    query = {}
    
    # Filter by order_id if provided
    if order_id:
        query["order_id"] = order_id
    
    # Handle special dual approval filters
    if filter_type == "replacement_approval_pending":
        query["replacement_approved"] = {"$ne": True}
        query["replacement_status"] = {"$nin": ["resolved", "rejected"]}
    elif filter_type == "pickup_approval_pending":
        query["pickup_approved"] = {"$ne": True}
        query["pickup_not_required"] = {"$ne": True}
        query["replacement_status"] = {"$nin": ["resolved", "rejected"]}
    elif filter_type == "pickups_pending":
        # Pickups approved but not yet picked up
        query["pickup_approved"] = True
        query["$or"] = [
            {"pickup_status": {"$in": [None, "approved", "pending"]}},
            {"pickup_status": {"$exists": False}}
        ]
        query["replacement_status"] = {"$nin": ["resolved", "rejected"]}
    elif filter_type == "pickups_in_transit":
        # Pickups that are picked up but not yet at warehouse
        query["pickup_approved"] = True
        query["pickup_status"] = "picked_up"  # Picked up = in transit to warehouse
        query["replacement_status"] = {"$nin": ["resolved", "rejected"]}
    elif filter_type == "shipments_pending":
        # Replacement approved but not yet shipped
        query["replacement_approved"] = True
        query["$or"] = [
            {"shipment_status": {"$in": [None, "approved", "pending"]}},
            {"shipment_status": {"$exists": False}}
        ]
        query["replacement_status"] = {"$nin": ["resolved", "rejected"]}
    elif filter_type == "shipments_in_transit":
        # Replacement shipped but not yet delivered
        query["replacement_approved"] = True
        query["shipment_status"] = "dispatched"
        query["replacement_status"] = {"$nin": ["resolved", "rejected"]}
    elif filter_type == "pickups_in_progress":
        # Legacy: any active pickup
        query["pickup_approved"] = True
        query["pickup_status"] = {"$nin": ["closed", "not_required", None]}
        query["replacement_status"] = {"$nin": ["resolved", "rejected"]}
    elif filter_type == "shipments_in_progress":
        # Legacy: any active shipment
        query["replacement_approved"] = True
        query["shipment_status"] = {"$nin": ["closed", None]}
        query["replacement_status"] = {"$nin": ["resolved", "rejected"]}
    # Handle both status filter and exclusion properly
    elif status and exclude_status:
        # Both provided: match status AND exclude specific one
        query["replacement_status"] = {"$eq": status, "$ne": exclude_status}
    elif status:
        # Only status filter
        query["replacement_status"] = status
    elif exclude_status:
        # Only exclusion
        query["replacement_status"] = {"$ne": exclude_status}
    
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
    
    # Define allowed transitions - PARALLEL WORKFLOWS ALLOWED
    REPLACEMENT_TRANSITIONS = {
        "requested": ["approved", "rejected"],
        "approved": ["picked_up", "pickup_not_required", "new_shipment_dispatched", "parts_shipped"],  # Can ship before pickup
        "picked_up": ["pickup_in_transit", "warehouse_received", "new_shipment_dispatched", "parts_shipped"],  # Parallel
        "pickup_in_transit": ["warehouse_received", "new_shipment_dispatched", "parts_shipped"],  # Parallel
        "pickup_not_required": ["new_shipment_dispatched", "parts_shipped", "delivered"],
        "warehouse_received": ["new_shipment_dispatched", "parts_shipped", "delivered"],
        "new_shipment_dispatched": ["delivered", "warehouse_received"],  # Can receive pickup after shipping
        "parts_shipped": ["delivered", "warehouse_received"],  # Can receive pickup after shipping
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
    if next_status == "picked_up" and not (pickup_date and pickup_tracking_id):
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
        "previous_status": current_status,  # Save for undo functionality
        "updated_at": now
    }
    
    # Set status-specific fields
    if next_status == "approved":
        update_data["approved_date"] = now
    elif next_status == "pickup_not_required":
        update_data["pickup_not_required"] = True
        # Set status directly to avoid requiring another call
        update_data["replacement_status"] = next_status
    elif next_status == "picked_up":
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

# FIX #3: Add DELETE endpoint for replacements
@router.delete("/{replacement_id}")
async def delete_replacement_request(
    replacement_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Delete a replacement request and clean up order references"""
    replacement = await db.replacement_requests.find_one({"id": replacement_id}, {"_id": 0})
    if not replacement:
        raise HTTPException(status_code=404, detail="Replacement request not found")
    
    # Clean up order - remove replacement references
    await db.orders.update_one(
        {"id": replacement["order_id"]},
        {"$set": {
            "replacement_requested": False,
            "replacement_status": None,
            "replacement_reason": None
        }}
    )
    
    # Delete replacement request
    result = await db.replacement_requests.delete_one({"id": replacement_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Replacement request not found")
    
    return {"message": "Replacement request deleted successfully", "deleted_count": result.deleted_count}


# BUG #3: Add UNDO endpoint for replacements
@router.patch("/{replacement_id}/undo")
async def undo_replacement_status(
    replacement_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Undo the last status change on a replacement request"""
    replacement = await db.replacement_requests.find_one({"id": replacement_id}, {"_id": 0})
    if not replacement:
        raise HTTPException(status_code=404, detail="Replacement request not found")
    
    previous_status = replacement.get("previous_status")
    if not previous_status:
        raise HTTPException(status_code=400, detail="No previous status to revert to")
    
    current_status = replacement.get("replacement_status")
    now = datetime.now(timezone.utc).isoformat()
    
    # Record undo in status history
    status_history = replacement.get("status_history", [])
    status_history.append({
        "status": previous_status,
        "timestamp": now,
        "changed_by": current_user.email,
        "notes": f"Undone from {current_status}",
        "is_undo": True
    })
    
    update_data = {
        "replacement_status": previous_status,
        "previous_status": None,  # Clear previous status after undo
        "updated_at": now,
        "status_history": status_history
    }
    
    # If undoing from resolved, also revert order status
    if current_status == "resolved":
        await db.orders.update_one(
            {"id": replacement["order_id"]},
            {"$set": {
                "replacement_status": previous_status,
                "status": "delivered"  # Revert order status
            }}
        )
    
    await db.replacement_requests.update_one(
        {"id": replacement_id},
        {"$set": update_data}
    )
    
    updated = await db.replacement_requests.find_one({"id": replacement_id}, {"_id": 0})
    return ReplacementRequest(**updated)

# BUG #6: Dual Approval - Approve Pickup
@router.patch("/{replacement_id}/approve-pickup")
async def approve_pickup(
    replacement_id: str,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Approve pickup of old/damaged product (separate from replacement approval)"""
    replacement = await db.replacement_requests.find_one({"id": replacement_id}, {"_id": 0})
    if not replacement:
        raise HTTPException(status_code=404, detail="Replacement request not found")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Update pickup approval and set pickup_status to approved
    status_history = replacement.get("status_history", [])
    status_history.append({
        "status": "pickup_approved",
        "timestamp": now,
        "changed_by": current_user.email,
        "notes": notes or "Pickup approved",
        "approval_type": "pickup"
    })
    
    update_data = {
        "pickup_approved": True,
        "pickup_approved_date": now,
        "pickup_approved_by": current_user.email,
        "pickup_status": "approved",  # Set pickup timeline status
        "updated_at": now,
        "status_history": status_history
    }
    
    await db.replacement_requests.update_one(
        {"id": replacement_id},
        {"$set": update_data}
    )
    
    updated = await db.replacement_requests.find_one({"id": replacement_id}, {"_id": 0})
    return {"message": "Pickup approved successfully", "replacement": ReplacementRequest(**updated)}

# BUG #6: Dual Approval - Approve Replacement Shipment
@router.patch("/{replacement_id}/approve-replacement")
async def approve_replacement_shipment(
    replacement_id: str,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Approve sending replacement product (separate from pickup approval)"""
    replacement = await db.replacement_requests.find_one({"id": replacement_id}, {"_id": 0})
    if not replacement:
        raise HTTPException(status_code=404, detail="Replacement request not found")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Update replacement approval and set shipment_status to approved
    status_history = replacement.get("status_history", [])
    status_history.append({
        "status": "replacement_approved",
        "timestamp": now,
        "changed_by": current_user.email,
        "notes": notes or "Replacement shipment approved",
        "approval_type": "replacement"
    })
    
    update_data = {
        "replacement_approved": True,
        "replacement_approved_date": now,
        "replacement_approved_by": current_user.email,
        "shipment_status": "approved",  # Set shipment timeline status
        "updated_at": now,
        "status_history": status_history
    }
    
    await db.replacement_requests.update_one(
        {"id": replacement_id},
        {"$set": update_data}
    )
    
    updated = await db.replacement_requests.find_one({"id": replacement_id}, {"_id": 0})
    return {"message": "Replacement shipment approved successfully", "replacement": ReplacementRequest(**updated)}

# BUG #5: Analytics endpoint for replacement counters
@router.get("/analytics/counts")
async def get_replacement_counts(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get counts for replacement dashboard counters"""
    # Open Replacement Requests (exclude resolved and rejected)
    open_count = await db.replacement_requests.count_documents({
        "replacement_status": {"$nin": ["resolved", "rejected"]}
    })
    
    # Replacements to be Shipped (approved but not yet dispatched)
    to_ship_count = await db.replacement_requests.count_documents({
        "replacement_status": {"$in": ["approved", "warehouse_received"]},
        "new_tracking_id": {"$in": [None, ""]},
        "parts_tracking_id": {"$in": [None, ""]}
    })
    
    # Replacements in Transit (dispatched but not delivered)
    in_transit_count = await db.replacement_requests.count_documents({
        "replacement_status": {"$in": ["new_shipment_dispatched", "parts_shipped"]}
    })
    
    # Pickups Pending (approved but not picked up, and pickup is required)
    pickups_pending_count = await db.replacement_requests.count_documents({
        "replacement_status": {"$in": ["requested", "approved"]},
        "pickup_not_required": {"$ne": True},
        "pickup_tracking_id": {"$in": [None, ""]}
    })
    
    return {
        "open_replacement_requests": open_count,
        "replacements_to_be_shipped": to_ship_count,
        "replacements_in_transit": in_transit_count,
        "pickups_pending": pickups_pending_count
    }


# BUG #6: Advance Pickup Timeline (separate from shipment)
@router.patch("/{replacement_id}/advance-pickup")
async def advance_pickup_timeline(
    replacement_id: str,
    next_status: str,
    # Pickup fields
    pickup_date: Optional[str] = None,
    pickup_tracking_id: Optional[str] = None,
    pickup_courier: Optional[str] = None,
    # Warehouse fields
    warehouse_received_date: Optional[str] = None,
    received_condition: Optional[str] = None,
    condition_notes: Optional[str] = None,
    condition_images: Optional[List[str]] = None,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Advance pickup timeline independently.
    Flow: pending -> approved -> picked_up -> in_transit -> warehouse_received -> condition_checked -> closed
    """
    replacement = await db.replacement_requests.find_one({"id": replacement_id}, {"_id": 0})
    if not replacement:
        raise HTTPException(status_code=404, detail="Replacement request not found")
    
    current_pickup_status = replacement.get("pickup_status", "pending")
    
    # Define pickup workflow transitions
    PICKUP_TRANSITIONS = {
        "pending": ["approved"],
        "approved": ["picked_up", "not_required"],
        "picked_up": ["in_transit", "warehouse_received"],
        "in_transit": ["warehouse_received"],
        "warehouse_received": ["condition_checked"],
        "condition_checked": ["closed"],
        "not_required": ["closed"],
        "closed": []
    }
    
    allowed = PICKUP_TRANSITIONS.get(current_pickup_status, [])
    if next_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition pickup from '{current_pickup_status}' to '{next_status}'. Allowed: {allowed}"
        )
    
    # Validate required fields
    if next_status == "picked_up" and not pickup_tracking_id:
        raise HTTPException(status_code=400, detail="pickup_tracking_id is required")
    
    if next_status == "condition_checked" and not received_condition:
        raise HTTPException(status_code=400, detail="received_condition ('mint' or 'damaged') is required")
    
    now = datetime.now(timezone.utc).isoformat()
    
    update_data = {
        "pickup_status": next_status,
        "updated_at": now
    }
    
    # Set fields based on status
    if next_status == "approved":
        update_data["pickup_approved"] = True
        update_data["pickup_approved_date"] = now
        update_data["pickup_approved_by"] = current_user.email
    elif next_status == "picked_up":
        update_data["pickup_date"] = pickup_date or now
        update_data["pickup_tracking_id"] = pickup_tracking_id
        update_data["pickup_courier"] = pickup_courier
    elif next_status == "warehouse_received":
        update_data["warehouse_received_date"] = warehouse_received_date or now
    elif next_status == "condition_checked":
        update_data["received_condition"] = received_condition
        update_data["condition_notes"] = condition_notes
        if condition_images:
            update_data["condition_images"] = condition_images
    elif next_status == "not_required":
        update_data["pickup_not_required"] = True
    
    # Add to status history
    status_history = replacement.get("status_history", [])
    status_history.append({
        "timeline": "pickup",
        "status": next_status,
        "timestamp": now,
        "changed_by": current_user.email,
        "notes": notes
    })
    update_data["status_history"] = status_history
    
    await db.replacement_requests.update_one(
        {"id": replacement_id},
        {"$set": update_data}
    )
    
    updated = await db.replacement_requests.find_one({"id": replacement_id}, {"_id": 0})
    return ReplacementRequest(**updated)

# BUG #6: Advance Shipment Timeline (separate from pickup)
@router.patch("/{replacement_id}/advance-shipment")
async def advance_shipment_timeline(
    replacement_id: str,
    next_status: str,
    # Shipment fields
    new_tracking_id: Optional[str] = None,
    new_courier: Optional[str] = None,
    items_sent_description: Optional[str] = None,
    parts_tracking_id: Optional[str] = None,
    parts_courier: Optional[str] = None,
    parts_description: Optional[str] = None,
    delivered_date: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Advance replacement shipment timeline independently.
    Flow: pending -> approved -> dispatched -> delivered -> closed
    """
    replacement = await db.replacement_requests.find_one({"id": replacement_id}, {"_id": 0})
    if not replacement:
        raise HTTPException(status_code=404, detail="Replacement request not found")
    
    current_shipment_status = replacement.get("shipment_status", "pending")
    
    # Define shipment workflow transitions
    SHIPMENT_TRANSITIONS = {
        "pending": ["approved"],
        "approved": ["dispatched", "parts_shipped"],
        "dispatched": ["delivered"],
        "parts_shipped": ["delivered"],
        "delivered": ["closed"],
        "closed": []
    }
    
    allowed = SHIPMENT_TRANSITIONS.get(current_shipment_status, [])
    if next_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition shipment from '{current_shipment_status}' to '{next_status}'. Allowed: {allowed}"
        )
    
    # Validate required fields
    if next_status == "dispatched" and not new_tracking_id:
        raise HTTPException(status_code=400, detail="new_tracking_id is required for dispatch")
    
    if next_status == "parts_shipped" and not parts_tracking_id:
        raise HTTPException(status_code=400, detail="parts_tracking_id is required")
    
    now = datetime.now(timezone.utc).isoformat()
    
    update_data = {
        "shipment_status": next_status,
        "updated_at": now
    }
    
    # Set fields based on status
    if next_status == "approved":
        update_data["replacement_approved"] = True
        update_data["replacement_approved_date"] = now
        update_data["replacement_approved_by"] = current_user.email
    elif next_status == "dispatched":
        update_data["new_tracking_id"] = new_tracking_id
        update_data["new_courier"] = new_courier
        update_data["items_sent_description"] = items_sent_description
        update_data["ship_date"] = now
    elif next_status == "parts_shipped":
        update_data["parts_tracking_id"] = parts_tracking_id
        update_data["parts_courier"] = parts_courier
        update_data["parts_description"] = parts_description
        update_data["ship_date"] = now
    elif next_status == "delivered":
        update_data["delivered_date"] = delivered_date or now
        update_data["delivery_confirmed"] = True
    elif next_status == "closed":
        update_data["resolved_date"] = now
        update_data["issue_resolved"] = True
        # Check if both timelines are closed
        pickup_status = replacement.get("pickup_status")
        if pickup_status in ["closed", "not_required", None]:
            update_data["replacement_status"] = "resolved"
    
    # Add to status history
    status_history = replacement.get("status_history", [])
    status_history.append({
        "timeline": "shipment",
        "status": next_status,
        "timestamp": now,
        "changed_by": current_user.email,
        "notes": notes
    })
    update_data["status_history"] = status_history
    
    await db.replacement_requests.update_one(
        {"id": replacement_id},
        {"$set": update_data}
    )
    
    updated = await db.replacement_requests.find_one({"id": replacement_id}, {"_id": 0})
    return ReplacementRequest(**updated)

# Update analytics counts to use new dual status fields
@router.get("/analytics/counts-v2")
async def get_replacement_counts_v2(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get counts for replacement dashboard with dual approval filters"""
    # Open Replacement Requests
    open_count = await db.replacement_requests.count_documents({
        "replacement_status": {"$nin": ["resolved", "rejected"]}
    })
    
    # Pickup Approval Pending
    pickup_approval_pending = await db.replacement_requests.count_documents({
        "pickup_approved": {"$ne": True},
        "pickup_not_required": {"$ne": True},
        "replacement_status": {"$nin": ["resolved", "rejected"]}
    })
    
    # Replacement Approval Pending
    replacement_approval_pending = await db.replacement_requests.count_documents({
        "replacement_approved": {"$ne": True},
        "replacement_status": {"$nin": ["resolved", "rejected"]}
    })
    
    # Pickups Pending (approved but not yet picked up)
    pickups_pending = await db.replacement_requests.count_documents({
        "pickup_approved": True,
        "$or": [
            {"pickup_status": {"$in": [None, "approved", "pending"]}},
            {"pickup_status": {"$exists": False}}
        ],
        "replacement_status": {"$nin": ["resolved", "rejected"]}
    })
    
    # Pickups In Transit (picked up but not at warehouse yet)
    pickups_in_transit = await db.replacement_requests.count_documents({
        "pickup_approved": True,
        "pickup_status": "picked_up",  # Picked up = in transit
        "replacement_status": {"$nin": ["resolved", "rejected"]}
    })
    
    # Shipments Pending (approved but not shipped yet)
    shipments_pending = await db.replacement_requests.count_documents({
        "replacement_approved": True,
        "$or": [
            {"shipment_status": {"$in": [None, "approved", "pending"]}},
            {"shipment_status": {"$exists": False}}
        ],
        "replacement_status": {"$nin": ["resolved", "rejected"]}
    })
    
    # Shipments In Transit (shipped but not delivered)
    shipments_in_transit = await db.replacement_requests.count_documents({
        "replacement_approved": True,
        "shipment_status": "dispatched",
        "replacement_status": {"$nin": ["resolved", "rejected"]}
    })
    
    return {
        "open_replacement_requests": open_count,
        "pickup_approval_pending": pickup_approval_pending,
        "replacement_approval_pending": replacement_approval_pending,
        "pickups_pending": pickups_pending,
        "pickups_in_transit": pickups_in_transit,
        "shipments_pending": shipments_pending,
        "shipments_in_transit": shipments_in_transit
    }
