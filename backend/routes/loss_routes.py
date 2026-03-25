from fastapi import APIRouter, Depends, HTTPException
from models import Order, LossConfiguration, LossConfigurationUpdate, OrderLossUpdate, User
from auth import get_current_active_user
from database import get_database
from datetime import datetime, timezone
from typing import Optional

router = APIRouter(prefix="/loss", tags=["loss-calculation"])

@router.get("/config", response_model=LossConfiguration)
async def get_loss_configuration(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get current loss calculation configuration"""
    config = await db.loss_configuration.find_one({"id": "loss_config"}, {"_id": 0})
    if not config:
        # Create default config
        default_config = {
            "id": "loss_config",
            "pfc_loss_percentage": 0.0,
            "resolved_cost_percentage": 15.0,
            "default_outbound_logistics": 100.0,
            "default_return_logistics": 100.0,
            "refunded_includes_product_cost_if_damage": True,
            "fraud_includes_product_and_logistics": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": "system"
        }
        await db.loss_configuration.insert_one(default_config)
        return LossConfiguration(**default_config)
    
    return LossConfiguration(**config)

@router.patch("/config")
async def update_loss_configuration(
    updates: LossConfigurationUpdate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Update loss calculation configuration variables"""
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = current_user.email
    
    await db.loss_configuration.update_one(
        {"id": "loss_config"},
        {"$set": update_data},
        upsert=True
    )
    
    return {"message": "Loss configuration updated successfully"}

@router.post("/calculate/{order_id}")
async def calculate_order_loss(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Auto-calculate loss for an order based on current configuration"""
    # Get order
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get config
    config = await db.loss_configuration.find_one({"id": "loss_config"}, {"_id": 0})
    if not config:
        config = {
            "pfc_loss_percentage": 0.0,
            "resolved_cost_percentage": 15.0,
            "default_outbound_logistics": 100.0,
            "default_return_logistics": 100.0,
            "refunded_includes_product_cost_if_damage": True,
            "fraud_includes_product_and_logistics": True
        }
    
    # Determine loss category
    loss_category = determine_loss_category(order)
    
    # Get order price
    price = order.get("price", 0) or 0
    
    # Initialize costs
    logistics_outbound = order.get("logistics_cost_outbound") or config["default_outbound_logistics"]
    logistics_return = order.get("logistics_cost_return") or config["default_return_logistics"]
    product_cost = order.get("product_cost") or (price * 0.6)  # Default 60% of price
    replacement_cost = order.get("replacement_parts_cost", 0)
    
    total_loss = 0.0
    
    # Calculate based on category
    if loss_category == "pfc":
        # PFC: 0% loss (just operational cost)
        total_loss = price * (config["pfc_loss_percentage"] / 100)
    
    elif loss_category == "resolved":
        # Resolved: 15% of price (configurable) + replacement cost
        total_loss = (price * (config["resolved_cost_percentage"] / 100)) + replacement_cost
    
    elif loss_category == "refunded":
        # Refunded: Logistics both ways
        total_loss = logistics_outbound + logistics_return
        
        # Add product cost if damage-related
        cancellation_reason = (order.get("cancellation_reason") or "").lower()
        if config["refunded_includes_product_cost_if_damage"]:
            if any(keyword in cancellation_reason for keyword in ["damage", "defective", "broken", "quality"]):
                total_loss += product_cost
    
    elif loss_category == "fraud":
        # Fraud: Product + both logistics
        total_loss = product_cost + logistics_outbound + logistics_return
    
    # Update order
    update_data = {
        "logistics_cost_outbound": logistics_outbound,
        "logistics_cost_return": logistics_return,
        "product_cost": product_cost,
        "replacement_parts_cost": replacement_cost,
        "total_loss": round(total_loss, 2),
        "loss_category": loss_category,
        "loss_calculation_method": "auto",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.orders.update_one({"id": order_id}, {"$set": update_data})
    
    return {
        "order_id": order_id,
        "loss_category": loss_category,
        "breakdown": {
            "logistics_outbound": logistics_outbound,
            "logistics_return": logistics_return,
            "product_cost": product_cost,
            "replacement_cost": replacement_cost,
            "total_loss": round(total_loss, 2)
        }
    }

@router.patch("/{order_id}")
async def update_order_loss(
    order_id: str,
    loss_update: OrderLossUpdate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Manually update loss calculation for an order"""
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    update_data = {k: v for k, v in loss_update.model_dump().items() if v is not None}
    update_data["loss_calculation_method"] = "manual"
    update_data["loss_edited_by"] = current_user.email
    update_data["loss_edited_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.orders.update_one({"id": order_id}, {"$set": update_data})
    
    return {"message": "Order loss updated successfully", "updated_by": current_user.email}

def determine_loss_category(order: dict) -> str:
    """Determine loss category based on order data. Never returns 'unknown'."""
    reason = (order.get("cancellation_reason") or "").lower()
    status = order.get("status", "")
    delivery_date = order.get("delivery_date")
    
    # Fraud detection (highest priority)
    if "cancelled and delivered" in reason or "fraud" in reason:
        return "fraud"
    
    # PFC: Pre-Fulfillment Cancellation
    if "pfc" in reason or "pre fulfillment" in reason:
        return "pfc"
    
    # PFC: Cancelled without delivery
    if status == "cancelled" and not delivery_date:
        return "pfc"
    
    # Resolved (delivered + solution provided)
    if status == "delivered" and any(keyword in reason for keyword in [
        "damage", "damaged and pending", "damaged and replaced",
        "hardware", "customer issue", "quality", "resolved", "replaced", "fixed"
    ]):
        return "resolved"
    
    # Refunded (default for all other return/cancel cases)
    return "refunded"
