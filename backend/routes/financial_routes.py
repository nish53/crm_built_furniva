from fastapi import APIRouter, Depends, HTTPException
from models import User
from models_advanced import OrderFinancials
from auth import get_current_active_user
from database import get_database
from datetime import datetime, timezone
from typing import Optional
import uuid

router = APIRouter(prefix="/financials", tags=["financials"])

@router.post("/calculate/{order_id}")
async def calculate_order_financials(
    order_id: str,
    product_cost: float,
    shipping_cost: float,
    packaging_cost: float = 0.0,
    installation_cost: float = 0.0,
    ads_cost: float = 0.0,
    account_management_charges: float = 0.0,
    other_charges: float = 0.0,
    marketplace_commission_rate: float = 15.0,
    apply_gst: bool = True,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Calculate complete financials for an order"""
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    selling_price = order.get("price", 0)
    
    # Calculate commission and fees
    marketplace_commission = selling_price * (marketplace_commission_rate / 100)
    tcs_tds = selling_price * 0.01  # 1% TCS
    payment_gateway_fee = selling_price * 0.02  # 2% gateway fee
    
    net_revenue = selling_price - marketplace_commission - tcs_tds - payment_gateway_fee
    
    # Calculate total costs (including new fields)
    total_cost = (product_cost + shipping_cost + packaging_cost + installation_cost + 
                  ads_cost + account_management_charges + other_charges)
    
    # Apply GST if enabled (18% fixed)
    gst_amount = 0.0
    if apply_gst:
        gst_amount = total_cost * 0.18
        total_cost += gst_amount
    
    # Calculate profit
    gross_profit = net_revenue - total_cost
    profit_margin = (gross_profit / selling_price * 100) if selling_price > 0 else 0
    contribution_margin = (gross_profit / net_revenue * 100) if net_revenue > 0 else 0
    
    # Expected settlement
    expected_settlement = net_revenue
    
    financial_data = {
        "id": str(uuid.uuid4()),
        "order_id": order_id,
        "order_number": order.get("order_number"),
        "selling_price": selling_price,
        "marketplace_commission": round(marketplace_commission, 2),
        "tcs_tds": round(tcs_tds, 2),
        "payment_gateway_fee": round(payment_gateway_fee, 2),
        "net_revenue": round(net_revenue, 2),
        "product_cost": product_cost,
        "shipping_cost": shipping_cost,
        "packaging_cost": packaging_cost,
        "installation_cost": installation_cost,
        "ads_cost": ads_cost,
        "account_management_charges": account_management_charges,
        "other_charges": other_charges,
        "gst_amount": round(gst_amount, 2),
        "rto_cost": 0.0,
        "claim_loss": 0.0,
        "total_cost": round(total_cost, 2),
        "gross_profit": round(gross_profit, 2),
        "profit_margin": round(profit_margin, 2),
        "contribution_margin": round(contribution_margin, 2),
        "expected_settlement": round(expected_settlement, 2),
        "claim_filed_amount": 0.0,
        "claim_recovered_amount": 0.0,
        "refund_given": 0.0,
        "refund_recovered": 0.0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Upsert
    await db.order_financials.update_one(
        {"order_id": order_id},
        {"$set": financial_data},
        upsert=True
    )
    
    return OrderFinancials(**financial_data)

@router.get("/order/{order_id}")
async def get_order_financials(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    financials = await db.order_financials.find_one({"order_id": order_id}, {"_id": 0})
    if not financials:
        raise HTTPException(status_code=404, detail="Financials not found")
    return OrderFinancials(**financials)

@router.patch("/settlement/{order_id}")
async def update_settlement(
    order_id: str,
    actual_settlement: float,
    settlement_date: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Update actual settlement received"""
    financials = await db.order_financials.find_one({"order_id": order_id}, {"_id": 0})
    if not financials:
        raise HTTPException(status_code=404, detail="Financials not found")
    
    expected = financials.get("expected_settlement", 0)
    variance = actual_settlement - expected
    
    await db.order_financials.update_one(
        {"order_id": order_id},
        {"$set": {
            "actual_settlement": actual_settlement,
            "settlement_date": settlement_date,
            "settlement_variance": round(variance, 2),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"variance": round(variance, 2), "message": "Settlement updated"}

@router.get("/profit-analysis")
async def get_profit_analysis(
    days: int = 30,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get aggregated profit analysis"""
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_revenue": {"$sum": "$selling_price"},
                "total_net_revenue": {"$sum": "$net_revenue"},
                "total_cost": {"$sum": "$total_cost"},
                "total_profit": {"$sum": "$gross_profit"},
                "avg_margin": {"$avg": "$profit_margin"},
                "total_orders": {"$sum": 1}
            }
        }
    ]
    
    result = await db.order_financials.aggregate(pipeline).to_list(1)
    return result[0] if result else {}

@router.get("/leakage-report")
async def get_leakage_report(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Identify refund and claim leakages"""
    pipeline = [
        {
            "$match": {
                "$or": [
                    {"settlement_variance": {"$lt": -100}},
                    {"refund_given": {"$gt": "$refund_recovered"}},
                    {"claim_filed_amount": {"$gt": "$claim_recovered_amount"}}
                ]
            }
        },
        {
            "$project": {
                "order_number": 1,
                "settlement_variance": 1,
                "refund_leakage": {"$subtract": ["$refund_given", "$refund_recovered"]},
                "claim_leakage": {"$subtract": ["$claim_filed_amount", "$claim_recovered_amount"]}
            }
        }
    ]
    
    leakages = await db.order_financials.aggregate(pipeline).to_list(100)
    return leakages


# Loss Calculation Configuration
DEFAULT_LOSS_CONFIG = {
    "resolved_cost_percentage": 15.0,  # % of product cost for resolved returns (replacement parts)
    "default_outbound_logistics": 150.0,  # Default outbound shipping cost
    "default_return_logistics": 120.0,  # Default return shipping cost  
    "refund_processing_fee": 50.0,  # Processing fee for refunds
    "qc_inspection_cost": 30.0,  # QC inspection cost per return
    "restocking_fee_percentage": 10.0,  # % for restocking refurbished items
    "fraud_investigation_cost": 500.0,  # Cost to investigate fraud cases
}

@router.get("/loss/config")
async def get_loss_config(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get loss calculation configuration variables"""
    config = await db.loss_config.find_one({}, {"_id": 0})
    if not config:
        # Return defaults if not configured
        return {"config": DEFAULT_LOSS_CONFIG, "is_default": True}
    return {"config": config, "is_default": False}

@router.patch("/loss/config")
async def update_loss_config(
    resolved_cost_percentage: Optional[float] = None,
    default_outbound_logistics: Optional[float] = None,
    default_return_logistics: Optional[float] = None,
    refund_processing_fee: Optional[float] = None,
    qc_inspection_cost: Optional[float] = None,
    restocking_fee_percentage: Optional[float] = None,
    fraud_investigation_cost: Optional[float] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Update loss calculation configuration"""
    # Get existing config or use defaults
    existing = await db.loss_config.find_one({}, {"_id": 0})
    if not existing:
        existing = DEFAULT_LOSS_CONFIG.copy()
    
    # Update only provided values
    update_data = {}
    if resolved_cost_percentage is not None:
        update_data["resolved_cost_percentage"] = resolved_cost_percentage
    if default_outbound_logistics is not None:
        update_data["default_outbound_logistics"] = default_outbound_logistics
    if default_return_logistics is not None:
        update_data["default_return_logistics"] = default_return_logistics
    if refund_processing_fee is not None:
        update_data["refund_processing_fee"] = refund_processing_fee
    if qc_inspection_cost is not None:
        update_data["qc_inspection_cost"] = qc_inspection_cost
    if restocking_fee_percentage is not None:
        update_data["restocking_fee_percentage"] = restocking_fee_percentage
    if fraud_investigation_cost is not None:
        update_data["fraud_investigation_cost"] = fraud_investigation_cost
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = current_user.email
    
    # Merge with existing
    final_config = {**existing, **update_data}
    
    # Upsert
    await db.loss_config.replace_one({}, final_config, upsert=True)
    
    return {"message": "Loss configuration updated", "config": final_config}

@router.post("/loss/calculate/{order_id}")
async def calculate_order_loss(
    order_id: str,
    logistics_outbound: Optional[float] = None,
    logistics_return: Optional[float] = None,
    product_cost: Optional[float] = None,
    replacement_cost: Optional[float] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Calculate loss for a specific order with returns/cancellations"""
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get loss config
    config = await db.loss_config.find_one({}, {"_id": 0})
    if not config:
        config = DEFAULT_LOSS_CONFIG
    
    # Get return info if exists
    return_req = await db.return_requests.find_one({"order_id": order_id}, {"_id": 0})
    
    # Calculate components
    outbound_cost = logistics_outbound or config.get("default_outbound_logistics", 150.0)
    return_cost = logistics_return or config.get("default_return_logistics", 120.0) if return_req else 0.0
    
    prod_cost = product_cost or order.get("price", 0) * 0.6  # Assume 60% cost if not provided
    
    # Replacement cost (for resolved returns)
    repl_cost = replacement_cost or 0.0
    if return_req and return_req.get("category") == "resolved":
        repl_cost = prod_cost * (config.get("resolved_cost_percentage", 15.0) / 100)
    
    # Additional costs
    additional_costs = 0.0
    if return_req:
        additional_costs += config.get("qc_inspection_cost", 30.0)
        if return_req.get("category") == "fraud":
            additional_costs += config.get("fraud_investigation_cost", 500.0)
        if return_req.get("return_status") == "refunded":
            additional_costs += config.get("refund_processing_fee", 50.0)
    
    # Total loss
    total_loss = outbound_cost + return_cost + prod_cost + repl_cost + additional_costs
    
    loss_data = {
        "order_id": order_id,
        "order_number": order.get("order_number"),
        "logistics_outbound": round(outbound_cost, 2),
        "logistics_return": round(return_cost, 2),
        "product_cost": round(prod_cost, 2),
        "replacement_cost": round(repl_cost, 2),
        "additional_costs": round(additional_costs, 2),
        "total_loss": round(total_loss, 2),
        "calculation_method": "auto" if not (logistics_outbound or product_cost) else "manual",
        "calculated_at": datetime.now(timezone.utc).isoformat(),
        "calculated_by": current_user.email
    }
    
    # Store in database
    await db.order_losses.update_one(
        {"order_id": order_id},
        {"$set": loss_data},
        upsert=True
    )
    
    return loss_data

@router.get("/loss/{order_id}")
async def get_order_loss(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get loss calculation for a specific order"""
    loss = await db.order_losses.find_one({"order_id": order_id}, {"_id": 0})
    if not loss:
        raise HTTPException(status_code=404, detail="No loss calculation found for this order")
    return loss
