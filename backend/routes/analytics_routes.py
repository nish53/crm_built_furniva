from fastapi import APIRouter, Depends
from models import User
from auth import get_current_active_user
from database import get_database
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/overview")
async def get_overview(
    days: int = 30,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get overview analytics for last N days"""
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    # Total orders
    total_orders = await db.orders.count_documents({
        "order_date": {"$gte": start_date}
    })
    
    # Revenue
    revenue_pipeline = [
        {
            "$match": {
                "order_date": {"$gte": start_date},
                "status": {"$nin": ["cancelled", "returned"]}
            }
        },
        {
            "$group": {
                "_id": None,
                "total": {"$sum": "$price"},
                "avg": {"$avg": "$price"}
            }
        }
    ]
    
    revenue_result = await db.orders.aggregate(revenue_pipeline).to_list(1)
    revenue = revenue_result[0] if revenue_result else {"total": 0, "avg": 0}
    
    # Orders by status
    status_pipeline = [
        {
            "$match": {
                "order_date": {"$gte": start_date}
            }
        },
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }
        }
    ]
    
    status_result = await db.orders.aggregate(status_pipeline).to_list(10)
    
    return {
        "period_days": days,
        "total_orders": total_orders,
        "total_revenue": round(revenue.get("total", 0), 2),
        "average_order_value": round(revenue.get("avg", 0), 2),
        "orders_by_status": status_result
    }

@router.get("/sales-trend")
async def get_sales_trend(
    days: int = 30,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get daily sales trend"""
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    pipeline = [
        {
            "$match": {
                "order_date": {"$gte": start_date},
                "status": {"$nin": ["cancelled"]}
            }
        },
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": {"$dateFromString": {"dateString": "$order_date"}}}},
                "orders": {"$sum": 1},
                "revenue": {"$sum": "$price"}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    
    result = await db.orders.aggregate(pipeline).to_list(days)
    return result

@router.get("/top-products")
async def get_top_products(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get top selling products"""
    pipeline = [
        {
            "$match": {
                "status": {"$nin": ["cancelled", "returned"]}
            }
        },
        {
            "$group": {
                "_id": "$sku",
                "product_name": {"$first": "$product_name"},
                "total_orders": {"$sum": 1},
                "total_quantity": {"$sum": "$quantity"},
                "total_revenue": {"$sum": "$price"}
            }
        },
        {"$sort": {"total_revenue": -1}},
        {"$limit": limit}
    ]
    
    result = await db.orders.aggregate(pipeline).to_list(limit)
    return result

@router.get("/returns-analysis")
async def get_returns_analysis(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Analyze returns by product and reason"""
    # Returns by product
    product_pipeline = [
        {
            "$match": {
                "status": "returned"
            }
        },
        {
            "$group": {
                "_id": "$sku",
                "product_name": {"$first": "$product_name"},
                "return_count": {"$sum": 1},
                "reasons": {"$push": "$cancellation_reason"}
            }
        },
        {"$sort": {"return_count": -1}},
        {"$limit": 10}
    ]
    
    by_product = await db.orders.aggregate(product_pipeline).to_list(10)
    
    # Returns by state
    state_pipeline = [
        {
            "$match": {
                "status": "returned"
            }
        },
        {
            "$group": {
                "_id": "$state",
                "return_count": {"$sum": 1}
            }
        },
        {"$sort": {"return_count": -1}}
    ]
    
    by_state = await db.orders.aggregate(state_pipeline).to_list(50)
    
    return {
        "by_product": by_product,
        "by_state": by_state
    }

@router.get("/channel-performance")
async def get_channel_performance(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Compare performance across channels"""
    pipeline = [
        {
            "$group": {
                "_id": "$channel",
                "total_orders": {"$sum": 1},
                "total_revenue": {"$sum": "$price"},
                "avg_order_value": {"$avg": "$price"},
                "returned_orders": {
                    "$sum": {"$cond": [{"$eq": ["$status", "returned"]}, 1, 0]}
                }
            }
        },
        {"$sort": {"total_revenue": -1}}
    ]
    
    result = await db.orders.aggregate(pipeline).to_list(10)
    
    # Calculate return rate
    for channel in result:
        channel["return_rate"] = round(
            (channel["returned_orders"] / channel["total_orders"] * 100) if channel["total_orders"] > 0 else 0,
            2
        )
    
    return result
