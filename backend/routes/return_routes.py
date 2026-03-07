from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from models import ReturnRequest, ReturnRequestCreate, ReturnStatus, User
from auth import get_current_active_user
from database import get_database
from datetime import datetime, timezone
from typing import List, Optional
import uuid

router = APIRouter(prefix="/return-requests", tags=["return-requests"])

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
    
    await db.return_requests.insert_one(return_dict)
    
    # Update order
    await db.orders.update_one(
        {"id": return_req.order_id},
        {"$set": {
            "return_requested": True,
            "return_reason": return_req.return_reason,
            "return_date": datetime.now(timezone.utc).isoformat()
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
