from fastapi import APIRouter, Depends, HTTPException
from models import EditHistoryEntry, EditHistoryCreate, FieldChange, User
from auth import get_current_active_user
from database import get_database
from datetime import datetime, timezone
from typing import List, Dict, Any
import uuid

router = APIRouter(prefix="/edit-history", tags=["edit-history"])

@router.get("/order/{order_id}", response_model=List[EditHistoryEntry])
async def get_order_edit_history(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get complete edit history for an order"""
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    history = await db.edit_history.find(
        {"order_id": order_id},
        {"_id": 0}
    ).sort("edited_at", -1).to_list(None)
    
    return history

@router.post("/", response_model=EditHistoryEntry)
async def create_edit_history(
    history: EditHistoryCreate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Manually create an edit history entry"""
    order = await db.orders.find_one({"id": history.order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    entry = {
        "id": str(uuid.uuid4()),
        "order_id": history.order_id,
        "order_number": order["order_number"],
        "changes": [change.model_dump() for change in history.changes],
        "edited_by": current_user.email,
        "edited_at": datetime.now(timezone.utc).isoformat(),
        "edit_reason": history.edit_reason
    }
    
    await db.edit_history.insert_one(entry)
    
    return EditHistoryEntry(**entry)

async def track_order_changes(
    order_id: str,
    old_order: Dict[str, Any],
    new_data: Dict[str, Any],
    user_email: str,
    edit_reason: str = None,
    db = None
):
    """
    Internal function to track changes when an order is updated
    Compares old and new values and creates edit history entry
    """
    if not db:
        return
    
    changes = []
    
    # Important fields to track
    tracked_fields = {
        "status": "Status",
        "cancellation_reason": "Cancellation Reason",
        "customer_name": "Customer Name",
        "phone": "Phone",
        "email": "Email",
        "address": "Address",
        "city": "City",
        "state": "State",
        "pincode": "Pincode",
        "price": "Price",
        "quantity": "Quantity",
        "sku": "SKU",
        "product_name": "Product Name",
        "courier_partner": "Courier Partner",
        "tracking_number": "Tracking Number",
        "dispatch_date": "Dispatch Date",
        "delivery_date": "Delivery Date",
        "order_date": "Order Date",
        "dispatch_by": "Dispatch By",
        "delivery_by": "Delivery By",
        "logistics_cost_outbound": "Outbound Logistics Cost",
        "logistics_cost_return": "Return Logistics Cost",
        "product_cost": "Product Cost",
        "total_loss": "Total Loss",
        "internal_notes": "Internal Notes"
    }
    
    for field, display_name in tracked_fields.items():
        if field in new_data:
            old_value = old_order.get(field)
            new_value = new_data[field]
            
            # Only track if value actually changed
            if old_value != new_value:
                # Special handling for status change: cancelled → delivered
                if field == "status" and old_value == "cancelled" and new_value == "delivered":
                    # Move cancellation_reason to history
                    if old_order.get("cancellation_reason"):
                        changes.append(FieldChange(
                            field_name="cancellation_reason",
                            old_value=old_order.get("cancellation_reason"),
                            new_value=None,
                            field_type="string"
                        ).model_dump())
                        
                        # Update the order to clear cancellation_reason
                        await db.orders.update_one(
                            {"id": order_id},
                            {"$set": {"cancellation_reason": None}}
                        )
                
                changes.append(FieldChange(
                    field_name=display_name,
                    old_value=str(old_value) if old_value is not None else None,
                    new_value=str(new_value) if new_value is not None else None,
                    field_type=type(new_value).__name__ if new_value is not None else "null"
                ).model_dump())
    
    # If there are changes, create history entry
    if changes:
        entry = {
            "id": str(uuid.uuid4()),
            "order_id": order_id,
            "order_number": old_order["order_number"],
            "changes": changes,
            "edited_by": user_email,
            "edited_at": datetime.now(timezone.utc).isoformat(),
            "edit_reason": edit_reason
        }
        
        await db.edit_history.insert_one(entry)
        
        return entry
    
    return None

@router.get("/recent", response_model=List[EditHistoryEntry])
async def get_recent_edits(
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get recent edit history across all orders"""
    history = await db.edit_history.find(
        {},
        {"_id": 0}
    ).sort("edited_at", -1).limit(limit).to_list(limit)
    
    return history

@router.get("/user/{user_email}", response_model=List[EditHistoryEntry])
async def get_user_edit_history(
    user_email: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get all edits made by a specific user"""
    history = await db.edit_history.find(
        {"edited_by": user_email},
        {"_id": 0}
    ).sort("edited_at", -1).to_list(None)
    
    return history
