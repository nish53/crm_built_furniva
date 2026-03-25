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

# Workflow transition map for 3-type return workflow
# Each return_type has its own allowed transitions
WORKFLOW_TRANSITIONS = {
    "pre_dispatch": {
        "requested": ["approved", "closed", "rejected"],
        "approved": ["closed"],
        "rejected": [],
        "closed": []
    },
    "in_transit": {
        "requested": ["approved", "closed", "rejected"],
        "approved": ["rto_in_transit", "closed"],
        "rto_in_transit": ["warehouse_received"],
        "warehouse_received": ["closed"],
        "rejected": [],
        "closed": []
    },
    "post_delivery": {
        "requested": ["accepted", "closed", "rejected"],
        "accepted": ["picked_up", "pickup_not_required"],
        "picked_up": ["pickup_in_transit", "warehouse_received"],  # Can go to warehouse directly
        "pickup_in_transit": ["warehouse_received"],
        "pickup_not_required": ["closed"],  # Skip directly to closed
        "warehouse_received": ["condition_checked"],
        "condition_checked": ["closed"],
        "rejected": [],
        "closed": []
    },
    # Legacy transitions for backward compatibility with old 12-stage workflow
    "legacy": {
        "requested": ["feedback_check", "authorized", "approved", "rejected", "closed", "cancelled"],
        "feedback_check": ["claim_filed", "authorized", "approved", "rejected", "closed", "cancelled"],
        "claim_filed": ["authorized", "approved", "rejected", "closed", "cancelled"],
        "authorized": ["return_initiated", "closed", "cancelled"],
        "return_initiated": ["in_transit", "closed", "cancelled"],
        "in_transit": ["warehouse_received", "closed"],
        "warehouse_received": ["qc_inspection", "closed"],
        "qc_inspection": ["claim_filing", "refund_processed", "closed"],
        "claim_filing": ["claim_status", "closed"],
        "claim_status": ["refund_processed", "closed"],
        "refund_processed": ["closed"],
        "closed": [],
        "rejected": [],
        "cancelled": [],
        "approved": ["pickup_scheduled", "return_initiated", "closed", "cancelled"],
        "pickup_scheduled": ["in_transit", "closed", "cancelled"],
        "received": ["inspected", "qc_inspection", "closed"],
        "inspected": ["refunded", "refund_processed", "replaced", "closed"],
        "refunded": ["closed"],
        "replaced": ["closed"],
    }
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
    cancellation_reason: str = None,  # NEW: Actual reason value from frontend
    notes: Optional[str] = None,  # NEW: Additional notes
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Create a new return request with 3-type workflow support.
    Automatically determines return_type based on order status:
    - pre_dispatch: order status is pending or confirmed
    - in_transit: order status is dispatched or in_transit  
    - post_delivery: order status is delivered
    """
    # Get order details
    order = await db.orders.find_one({"id": return_req.order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order_status = order.get("status", "pending")
    
    # CONTEXT-DEPENDENT: Determine return_type based on order status
    if order_status in ["pending", "confirmed"]:
        return_type = "pre_dispatch"
    elif order_status in ["dispatched", "in_transit"]:
        return_type = "in_transit"
    elif order_status == "delivered":
        return_type = "post_delivery"
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot create return for order with status '{order_status}'"
        )
    
    # Validate cancellation_reason is provided
    if not cancellation_reason:
        raise HTTPException(
            status_code=400,
            detail="cancellation_reason is required"
        )
    
    # Classify the return category for loss calculation
    category = classify_return_category(
        return_reason=cancellation_reason,
        status=order_status,
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
    return_dict["category"] = "in_progress"
    
    # NEW FIELDS for 3-type workflow
    return_dict["return_type"] = return_type
    return_dict["cancellation_reason"] = cancellation_reason
    return_dict["notes"] = notes
    return_dict["pickup_not_required"] = False
    
    return_dict["status_history"] = [{
        "from_status": None,
        "to_status": ReturnStatus.REQUESTED,
        "changed_at": datetime.now(timezone.utc).isoformat(),
        "changed_by": current_user.email,
        "return_type": return_type,
        "notes": notes
    }]
    
    await db.return_requests.insert_one(return_dict)
    
    # Update order - sync cancellation_reason but DON'T change status yet
    # Order status should only change when return is closed/completed
    await db.orders.update_one(
        {"id": return_req.order_id},
        {"$set": {
            "return_requested": True,
            "return_reason": cancellation_reason,
            "cancellation_reason": cancellation_reason,
            "return_date": datetime.now(timezone.utc).isoformat(),
            "loss_category": category,
            "previous_status": order_status  # Save current status for potential reversion
            # DO NOT SET status to "cancelled" here - only when return is closed
        }}
    )
    
    return ReturnRequest(**return_dict)

@router.get("/", response_model=List[ReturnRequest])
async def get_return_requests(
    status: Optional[ReturnStatus] = None,
    exclude_status: Optional[str] = None,  # NEW: exclude certain statuses
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get all return requests with option to exclude closed returns"""
    query = {}
    
    # Handle both status filter and exclusion properly
    if status and exclude_status:
        # Both provided: match status AND exclude specific one
        query["return_status"] = {"$eq": status, "$ne": exclude_status}
    elif status:
        # Only status filter
        query["return_status"] = status
    elif exclude_status:
        # Only exclusion
        query["return_status"] = {"$ne": exclude_status}
    
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
    # NEW: Common fields for all types
    notes: Optional[str] = None,
    # Pre-dispatch fields
    approved_by: Optional[str] = None,
    # In-transit RTO fields
    rto_tracking_number: Optional[str] = None,
    rto_courier: Optional[str] = None,
    # Post-delivery pickup fields
    pickup_date: Optional[str] = None,
    pickup_tracking_id: Optional[str] = None,
    pickup_courier: Optional[str] = None,
    pickup_not_required: Optional[bool] = None,
    # Warehouse fields (both in-transit and post-delivery)
    warehouse_received_date: Optional[str] = None,
    # Post-delivery condition check fields
    received_condition: Optional[str] = None,  # "mint" or "damaged"
    condition_notes: Optional[str] = None,
    # Legacy fields for backward compatibility
    tracking_number: Optional[str] = None,
    courier_partner: Optional[str] = None,
    refund_amount: Optional[float] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Advance return through 3-type workflow with context-aware validation.
    - pre_dispatch: requested → approved/rejected → closed
    - in_transit: requested → approved → rto_in_transit → warehouse_received → closed
    - post_delivery: requested → accepted → pickup_scheduled/pickup_not_required → warehouse_received → condition_checked → closed
    """
    return_req = await db.return_requests.find_one({"id": return_id}, {"_id": 0})
    if not return_req:
        raise HTTPException(status_code=404, detail="Return request not found")
    
    current_status = return_req.get("return_status", "requested")
    return_type = return_req.get("return_type", "legacy")
    
    # Get allowed transitions for this return type
    if return_type in WORKFLOW_TRANSITIONS:
        allowed = WORKFLOW_TRANSITIONS[return_type].get(current_status, [])
    else:
        # Fallback to legacy workflow for old return requests
        allowed = WORKFLOW_TRANSITIONS["legacy"].get(current_status, [])
    
    if next_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{current_status}' to '{next_status}' for {return_type} return. Allowed: {allowed}"
        )
    
    # Context-aware validation based on return_type and next_status
    if return_type == "in_transit":
        if next_status == "rto_in_transit" and not rto_tracking_number:
            raise HTTPException(
                status_code=400,
                detail="rto_tracking_number is required for RTO in-transit status"
            )
    
    elif return_type == "post_delivery":
        if next_status == "picked_up" and not (pickup_date or pickup_tracking_id):
            raise HTTPException(
                status_code=400,
                detail="pickup_date and pickup_tracking_id are required for picked_up status"
            )
        if next_status == "condition_checked" and not received_condition:
            raise HTTPException(
                status_code=400,
                detail="received_condition ('mint' or 'damaged') is required for condition_checked status"
            )
    
    # Build update data
    now = datetime.now(timezone.utc).isoformat()
    update_data = {
        "return_status": next_status,
        "previous_status": current_status,
        "updated_at": now
    }
    
    # Set status-specific fields based on return_type
    if return_type == "pre_dispatch":
        if next_status == "approved":
            update_data["approved_date"] = now
            update_data["approved_by"] = approved_by or current_user.email
    
    elif return_type == "in_transit":
        if next_status == "approved":
            update_data["approved_date"] = now
            update_data["approved_by"] = current_user.email
        elif next_status == "rto_in_transit":
            update_data["rto_tracking_number"] = rto_tracking_number
            update_data["rto_courier"] = rto_courier
        elif next_status == "warehouse_received":
            update_data["warehouse_received_date"] = warehouse_received_date or now
    
    elif return_type == "post_delivery":
        if next_status == "accepted":
            update_data["approved_date"] = now
            update_data["approved_by"] = current_user.email
        elif next_status == "pickup_not_required":
            update_data["pickup_not_required"] = True
            # Skip directly to closed
            update_data["return_status"] = "closed"
            update_data["closed_date"] = now
            update_data["closed_by"] = current_user.email
        elif next_status == "picked_up":
            update_data["pickup_date"] = pickup_date
            update_data["pickup_tracking_id"] = pickup_tracking_id
            update_data["pickup_courier"] = pickup_courier
        elif next_status == "warehouse_received":
            update_data["warehouse_received_date"] = warehouse_received_date or now
        elif next_status == "condition_checked":
            update_data["received_condition"] = received_condition
            update_data["condition_notes"] = condition_notes
    
    # Add notes if provided
    if notes:
        update_data["notes"] = notes
    
    # Update status history
    status_history = return_req.get("status_history", [])
    status_history.append({
        "from_status": current_status,
        "to_status": next_status,
        "changed_at": now,
        "changed_by": current_user.email,
        "notes": notes,
        "return_type": return_type
    })
    update_data["status_history"] = status_history
    
    # Update return request
    await db.return_requests.update_one(
        {"id": return_id},
        {"$set": update_data}
    )
    
    # Get order to check previous_status
    order = await db.orders.find_one({"id": return_req["order_id"]}, {"_id": 0})
    
    # Handle status changes based on return workflow outcome
    if next_status == "rejected":
        # FIX #2: When rejected, revert order status to previous status
        previous_order_status = order.get("previous_status", "delivered")
        await db.orders.update_one(
            {"id": return_req["order_id"]},
            {"$set": {
                "status": previous_order_status,  # Revert to original status
                "return_requested": False,
                "return_status": "rejected",
                "return_reason": None,
                "cancellation_reason": None
            }}
        )
    elif next_status == "closed" or update_data.get("return_status") == "closed":
        # FIX #1: Only move to cancelled when return is CLOSED (completed)
        await db.orders.update_one(
            {"id": return_req["order_id"]},
            {"$set": {
                "status": "cancelled",
                "return_status": "closed",
                "closed_date": now
            }}
        )
    
    # Fetch and return updated return request
    updated_return = await db.return_requests.find_one({"id": return_id}, {"_id": 0})
    return ReturnRequest(**updated_return)

@router.get("/{return_id}/workflow-stages")
async def get_workflow_stages(
    return_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get allowed next workflow stages for a return request based on return_type"""
    return_req = await db.return_requests.find_one({"id": return_id}, {"_id": 0})
    if not return_req:
        raise HTTPException(status_code=404, detail="Return request not found")
    
    current_status = return_req.get("return_status", "requested")
    return_type = return_req.get("return_type", "legacy")
    
    # Get allowed transitions for this return type
    if return_type in WORKFLOW_TRANSITIONS:
        allowed = WORKFLOW_TRANSITIONS[return_type].get(current_status, [])
    else:
        # Fallback to legacy workflow
        allowed = WORKFLOW_TRANSITIONS["legacy"].get(current_status, [])
    
    return {
        "return_id": return_id,
        "return_type": return_type,
        "current_status": current_status,
        "allowed_transitions": allowed,
        "is_terminal": len(allowed) == 0,
        "workflow_description": _get_workflow_description(return_type)
    }

def _get_workflow_description(return_type: str) -> dict:
    """Get human-readable workflow description"""
    descriptions = {
        "pre_dispatch": {
            "name": "Pre-Dispatch Cancellation",
            "flow": "requested → approved/rejected → closed"
        },
        "in_transit": {
            "name": "In-Transit RTO (Return to Origin)",
            "flow": "requested → approved → rto_in_transit → warehouse_received → closed"
        },
        "post_delivery": {
            "name": "Post-Delivery Return",
            "flow": "requested → accepted → pickup_scheduled/pickup_not_required → warehouse_received → condition_checked → closed"
        },
        "legacy": {
            "name": "Legacy 12-Stage Workflow",
            "flow": "requested → ... → closed"
        }
    }
    return descriptions.get(return_type, {"name": "Unknown", "flow": "Unknown"})

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

# FIX #3: Add DELETE endpoint for returns
@router.delete("/{return_id}")
async def delete_return_request(
    return_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Delete a return request and clean up order references"""
    return_req = await db.return_requests.find_one({"id": return_id}, {"_id": 0})
    if not return_req:
        raise HTTPException(status_code=404, detail="Return request not found")
    
    # Clean up order - remove return references
    await db.orders.update_one(
        {"id": return_req["order_id"]},
        {"$set": {
            "return_requested": False,
            "return_status": None,
            "return_reason": None,
            "cancellation_reason": None
        }}
    )
    
    # Delete return request
    result = await db.return_requests.delete_one({"id": return_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Return request not found")
    
    return {"message": "Return request deleted successfully", "deleted_count": result.deleted_count}
