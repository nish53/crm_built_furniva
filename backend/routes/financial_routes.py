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
    marketplace_commission_rate: float = 15.0,
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
    
    # Calculate total costs
    total_cost = product_cost + shipping_cost + packaging_cost + installation_cost
    
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
