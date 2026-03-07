from fastapi import APIRouter, Depends, HTTPException, Query
from models import Order, User
from auth import get_current_active_user
from database import get_database
from typing import List, Optional
from datetime import datetime, timezone

router = APIRouter(prefix="/returns", tags=["returns"])

@router.get("/")
async def get_returns(
    reason_filter: Optional[str] = None,
    fraud_only: bool = False,
    damage_only: bool = False,
    pending_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get all returns/cancelled orders with smart filtering"""
    query = {
        "$or": [
            {"status": "returned"},
            {"status": "cancelled"},
            {"return_requested": True},
            {"cancellation_reason": {"$exists": True, "$ne": ""}}
        ]
    }
    
    # Smart filtering based on cancellation reason
    if fraud_only:
        # Fraud: cancelled/delivered after actual delivery
        query["$and"] = [
            {"cancellation_reason": {"$in": ["cancelled", "delivered", "Fraud", "fraud"]}},
            {"$or": [
                {"status": "cancelled"},
                {"delivery_date": {"$exists": True, "$ne": None}}
            ]}
        ]
    
    if damage_only:
        # Damage related returns
        query["cancellation_reason"] = {"$regex": "damage|Damage|hardware|Hardware", "$options": "i"}
    
    if pending_only:
        # Pending action items
        query["cancellation_reason"] = {"$regex": "pending|status pending", "$options": "i"}
    
    if reason_filter:
        query["cancellation_reason"] = {"$regex": reason_filter, "$options": "i"}
    
    orders = await db.orders.find(query, {"_id": 0}).sort("order_date", -1).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with smart flags
    for order in orders:
        order["smart_flags"] = classify_return(order)
    
    return {
        "items": orders,
        "total": await db.orders.count_documents(query)
    }

@router.get("/analytics")
async def get_returns_analytics(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get returns analytics and metrics"""
    
    # Get all returns/cancellations
    returns_query = {
        "$or": [
            {"status": "returned"},
            {"status": "cancelled"},
            {"return_requested": True},
            {"cancellation_reason": {"$exists": True, "$ne": ""}}
        ]
    }
    
    returns = await db.orders.find(returns_query, {"_id": 0}).to_list(None)
    
    # Total orders for rate calculation
    total_orders = await db.orders.count_documents({})
    
    # Analytics
    total_returns = len(returns)
    return_rate = (total_returns / total_orders * 100) if total_orders > 0 else 0
    
    # By reason
    reason_breakdown = {}
    fraud_count = 0
    damage_count = 0
    pfc_count = 0
    replacement_count = 0
    
    for order in returns:
        reason = order.get("cancellation_reason", "Unknown")
        reason_breakdown[reason] = reason_breakdown.get(reason, 0) + 1
        
        # Classify
        flags = classify_return(order)
        if "fraud" in flags:
            fraud_count += 1
        if "damage" in flags:
            damage_count += 1
        if "pfc" in flags:
            pfc_count += 1
        if "replacement" in flags:
            replacement_count += 1
    
    # By product
    product_returns = {}
    for order in returns:
        sku = order.get("master_sku") or order.get("sku", "Unknown")
        product_returns[sku] = product_returns.get(sku, 0) + 1
    
    # Top problematic products
    top_products = sorted(product_returns.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # By courier
    courier_returns = {}
    for order in returns:
        courier = order.get("courier_partner", "Unknown")
        if courier:
            courier_returns[courier] = courier_returns.get(courier, 0) + 1
    
    return {
        "summary": {
            "total_returns": total_returns,
            "total_orders": total_orders,
            "return_rate": round(return_rate, 2),
            "fraud_count": fraud_count,
            "damage_count": damage_count,
            "pfc_count": pfc_count,
            "replacement_count": replacement_count
        },
        "by_reason": reason_breakdown,
        "top_problematic_products": [{"sku": k, "count": v} for k, v in top_products],
        "by_courier": courier_returns
    }

@router.post("/{order_id}/action")
async def take_return_action(
    order_id: str,
    action: str,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Take action on a return (approve refund, schedule replacement, etc.)"""
    
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    update_data = {
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if action == "approve_refund":
        update_data["return_status"] = "refund_approved"
        if notes:
            update_data["internal_notes"] = f"{order.get('internal_notes', '')}\n[REFUND APPROVED] {notes}"
    
    elif action == "schedule_replacement":
        update_data["return_status"] = "replacement_scheduled"
        if notes:
            update_data["internal_notes"] = f"{order.get('internal_notes', '')}\n[REPLACEMENT SCHEDULED] {notes}"
    
    elif action == "mark_fraud":
        update_data["return_status"] = "fraud_flagged"
        if notes:
            update_data["internal_notes"] = f"{order.get('internal_notes', '')}\n[FRAUD ALERT] {notes}"
    
    elif action == "close":
        update_data["return_status"] = "closed"
        if notes:
            update_data["internal_notes"] = f"{order.get('internal_notes', '')}\n[CLOSED] {notes}"
    
    await db.orders.update_one({"id": order_id}, {"$set": update_data})
    
    return {"message": f"Action '{action}' completed successfully", "order_id": order_id}

def classify_return(order: dict) -> List[str]:
    """Classify return/cancellation with smart flags"""
    flags = []
    
    reason = order.get("cancellation_reason") or ""  # Handle None values
    reason = reason.lower() if reason else ""
    status = order.get("status", "")
    delivery_date = order.get("delivery_date")
    
    # Fraud - either explicit fraud keyword or cancelled/delivered with actual delivery
    if "fraud" in reason or (reason in ["cancelled", "delivered"] and delivery_date):
        flags.append("fraud")
    
    # PFC (Pre-Fulfillment Cancel) - cancelled before shipping (but not fraud)
    elif "pfc" in reason or (status == "cancelled" and not delivery_date):
        flags.append("pfc")
    
    # Damage related
    if "damage" in reason or "hardware" in reason:
        flags.append("damage")
        
        # Needs replacement
        if "replaced" in reason or "replacement" in reason:
            flags.append("replacement")
    
    # Pending action
    if "pending" in reason or "status pending" in reason:
        flags.append("pending_action")
    
    # Delay related
    if "delay" in reason:
        flags.append("delay")
    
    # Customer issue
    if "customer" in reason:
        flags.append("customer_issue")
    
    return flags
