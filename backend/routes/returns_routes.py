from fastapi import APIRouter, Depends, HTTPException, Query
from models import Order, User
from auth import get_current_active_user
from database import get_database
from typing import List, Optional
from datetime import datetime, timezone

router = APIRouter(prefix="/returns", tags=["returns"])

@router.get("/")
async def get_returns(
    category: Optional[str] = None,  # pfc, resolved, refunded, fraud, all
    reason_filter: Optional[str] = None,
    pincode_filter: Optional[str] = None,
    sku_filter: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get all returns/cancelled orders with smart filtering based on business logic"""
    
    # Base query: orders with cancellation_reason OR status=returned/cancelled
    query = {
        "$or": [
            {"status": "returned"},
            {"status": "cancelled"},
            {"return_requested": True},
            {"cancellation_reason": {"$exists": True, "$ne": "", "$nin": [None]}}
        ]
    }
    
    # Category-based filtering
    if category == "pfc":
        # PFC: Pre-Fulfillment Cancel - not dispatched
        query["cancellation_reason"] = {"$regex": "PFC|pfc", "$options": "i"}
        query["status"] = "cancelled"
    
    elif category == "resolved":
        # Resolved: Delivered + solution provided (no refund)
        query["status"] = "delivered"
        query["cancellation_reason"] = {
            "$regex": "damage|hardware|customer issue|damaged and pending|damaged and replaced",
            "$options": "i"
        }
    
    elif category == "refunded":
        # Refunded: Cancelled (excluding PFC) = full loss
        query["status"] = "cancelled"
        query["cancellation_reason"] = {
            "$not": {"$regex": "PFC|pfc", "$options": "i"}
        }
    
    elif category == "fraud":
        # Fraud/Logistics Error: "cancelled and delivered" - double loss
        query["cancellation_reason"] = {"$regex": "cancelled and delivered", "$options": "i"}
    
    # Additional filters
    if reason_filter:
        query["cancellation_reason"] = {"$regex": reason_filter, "$options": "i"}
    
    if pincode_filter:
        query["pincode"] = {"$regex": pincode_filter, "$options": "i"}
    
    if sku_filter:
        query["$or"] = [
            {"master_sku": {"$regex": sku_filter, "$options": "i"}},
            {"sku": {"$regex": sku_filter, "$options": "i"}}
        ]
    
    total = await db.orders.count_documents(query)
    orders = await db.orders.find(query, {"_id": 0}).sort("order_date", -1).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with smart classification
    for order in orders:
        order["category"] = classify_return_category(order)
        order["refund_loss"] = calculate_refund_loss(order)
    
    return {
        "items": orders,
        "total": total
    }

@router.get("/analytics")
async def get_returns_analytics(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get comprehensive returns analytics with business intelligence"""
    
    # Get all returns/cancellations
    returns_query = {
        "$or": [
            {"status": "returned"},
            {"status": "cancelled"},
            {"return_requested": True},
            {"cancellation_reason": {"$exists": True, "$ne": "", "$nin": [None]}}
        ]
    }
    
    returns = await db.orders.find(returns_query, {"_id": 0}).to_list(None)
    total_orders = await db.orders.count_documents({})
    
    # Initialize counters
    total_returns = len(returns)
    return_rate = (total_returns / total_orders * 100) if total_orders > 0 else 0
    
    pfc_count = 0
    pfc_loss = 0
    
    resolved_count = 0
    resolved_cost = 0
    
    refunded_count = 0
    refunded_loss = 0
    
    fraud_count = 0
    fraud_loss = 0
    
    # By reason
    reason_breakdown = {}
    
    # By product
    product_returns = {}
    product_refund_loss = {}
    
    # By pincode
    pincode_returns = {}
    pincode_damage = {}
    
    # By courier
    courier_returns = {}
    courier_damage = {}
    
    # Process each return
    for order in returns:
        category = classify_return_category(order)
        reason = order.get("cancellation_reason", "Unknown")
        price = order.get("price", 0) or 0
        sku = order.get("master_sku") or order.get("sku", "Unknown")
        pincode = order.get("pincode", "Unknown")
        courier = order.get("courier_partner", "Unknown")
        
        # Categorize and calculate actual loss
        if category == "pfc":
            pfc_count += 1
            pfc_loss += order.get("total_loss", price * 0.1)  # Use actual or fallback
        
        elif category == "resolved":
            resolved_count += 1
            resolved_cost += order.get("total_loss", price * 0.15)  # Use actual or fallback
        
        elif category == "refunded":
            refunded_count += 1
            refunded_loss += order.get("total_loss", price)  # Use actual or fallback
        
        elif category == "fraud":
            fraud_count += 1
            fraud_loss += order.get("total_loss", price * 2)  # Use actual or fallback
        
        # By reason
        reason_breakdown[reason] = reason_breakdown.get(reason, 0) + 1
        
        # By product
        product_returns[sku] = product_returns.get(sku, 0) + 1
        if category in ["refunded", "fraud"]:
            product_refund_loss[sku] = product_refund_loss.get(sku, 0) + price
        
        # By pincode
        pincode_returns[pincode] = pincode_returns.get(pincode, 0) + 1
        if "damage" in reason.lower():
            pincode_damage[pincode] = pincode_damage.get(pincode, 0) + 1
        
        # By courier
        if courier:
            courier_returns[courier] = courier_returns.get(courier, 0) + 1
            if "damage" in reason.lower():
                courier_damage[courier] = courier_damage.get(courier, 0) + 1
    
    # Calculate total loss
    total_loss = pfc_loss + resolved_cost + refunded_loss + fraud_loss
    
    # Top problematic products (by refund loss, not just count)
    top_products_by_loss = sorted(product_refund_loss.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Top problematic pincodes (by return rate)
    top_pincodes = sorted(pincode_returns.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Most damaged pincodes
    top_damage_pincodes = sorted(pincode_damage.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "summary": {
            "total_returns": total_returns,
            "total_orders": total_orders,
            "return_rate": round(return_rate, 2),
            "total_loss": round(total_loss, 2),
            
            "pfc_count": pfc_count,
            "pfc_loss": round(pfc_loss, 2),
            
            "resolved_count": resolved_count,
            "resolved_cost": round(resolved_cost, 2),
            
            "refunded_count": refunded_count,
            "refunded_loss": round(refunded_loss, 2),
            
            "fraud_count": fraud_count,
            "fraud_loss": round(fraud_loss, 2)
        },
        "by_reason": reason_breakdown,
        "top_products_by_loss": [{"sku": k, "loss": round(v, 2)} for k, v in top_products_by_loss],
        "top_problematic_pincodes": [{"pincode": k, "count": v} for k, v in top_pincodes],
        "top_damage_pincodes": [{"pincode": k, "damage_count": v} for k, v in top_damage_pincodes],
        "courier_performance": {
            "returns": courier_returns,
            "damage": courier_damage
        }
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

def classify_return_category(order: dict) -> str:
    """Classify return into business categories - handles both historical and new orders"""
    
    reason = (order.get("cancellation_reason") or "").lower()
    status = order.get("status", "")
    
    # Category 1: PFC (Pre-Fulfillment Cancel)
    if "pfc" in reason or "pre fulfillment" in reason:
        return "pfc"
    
    # Category 4: Fraud/Logistics Error
    if "cancelled and delivered" in reason or "fraud" in reason:
        return "fraud"
    
    # Category 2: Resolved (Delivered + solution provided, no refund)
    # Historical: "damaged and replaced" OR status=delivered with damage-related reason
    if status == "delivered":
        if any(keyword in reason for keyword in [
            "damaged and replaced", "damaged and pending",
            "damage", "quality", "hardware", "customer issue"
        ]):
            return "resolved"
    
    # Category 3: Refunded (Cancelled excluding PFC)
    if status == "cancelled":
        if "pfc" not in reason and "pre fulfillment" not in reason:
            return "refunded"
    
    # Default for unclear cases
    if status == "cancelled":
        return "refunded"  # Default cancelled orders to refunded
    
    return "unknown"

def calculate_refund_loss(order: dict) -> float:
    """Calculate actual loss based on category"""
    price = order.get("price", 0) or 0
    category = classify_return_category(order)
    
    if category == "pfc":
        return price * 0.1  # 10% operational cost
    elif category == "resolved":
        return price * 0.2  # 20% solution cost (replacement/carpenter)
    elif category == "refunded":
        return price  # Full refund
    elif category == "fraud":
        return price * 2  # Product + refund = double loss
    
    return 0

def classify_return(order: dict) -> List[str]:
    """Legacy function - kept for backward compatibility"""
    flags = []
    
    reason = order.get("cancellation_reason") or ""  # Handle None values
    reason = reason.lower() if reason else ""
    
    category = classify_return_category(order)
    flags.append(category)
    
    # Add descriptive flags
    if "pfc" in reason:
        flags.append("pfc")
    if "damage" in reason:
        flags.append("damage")
    if "delay" in reason:
        flags.append("delay")
    if "hardware" in reason:
        flags.append("hardware")
    if "customer" in reason:
        flags.append("customer_issue")
    if "fraud" in reason or "cancelled and delivered" in reason:
        flags.append("fraud")
    
    return flags
