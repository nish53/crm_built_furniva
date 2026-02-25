from fastapi import APIRouter, Depends
from models import DashboardStats, User
from auth import get_current_active_user
from database import get_database
from datetime import datetime, date, timezone

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    today = datetime.now(timezone.utc).date().isoformat()
    
    total_orders = await db.orders.count_documents({})
    pending_orders = await db.orders.count_documents({"status": "pending"})
    
    dispatched_today_count = await db.orders.count_documents({
        "dispatch_date": {"$gte": today}
    })
    
    pending_tasks = await db.tasks.count_documents({"status": "pending"})
    
    pending_calls = await db.orders.count_documents({
        "dc1_called": False,
        "status": "confirmed"
    })
    
    low_stock_items = await db.products.count_documents({
        "$expr": {"$lte": ["$stock_quantity", "$reorder_level"]}
    })
    
    pending_claims = await db.claims.count_documents({"status": "filed"})
    
    revenue_pipeline = [
        {
            "$match": {
                "order_date": {"$gte": today},
                "status": {"$nin": ["cancelled", "returned"]}
            }
        },
        {
            "$group": {
                "_id": None,
                "total": {"$sum": "$price"}
            }
        }
    ]
    
    revenue_result = await db.orders.aggregate(revenue_pipeline).to_list(1)
    revenue_today = revenue_result[0]["total"] if revenue_result else 0.0
    
    return DashboardStats(
        total_orders=total_orders,
        pending_orders=pending_orders,
        dispatched_today=dispatched_today_count,
        pending_tasks=pending_tasks,
        pending_calls=pending_calls,
        low_stock_items=low_stock_items,
        pending_claims=pending_claims,
        revenue_today=revenue_today
    )

@router.get("/recent-orders")
async def get_recent_orders(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    orders = await db.orders.find({}, {"_id": 0}).sort("created_at", -1).limit(10).to_list(10)
    return orders

@router.get("/analytics/sales-by-state")
async def get_sales_by_state(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    pipeline = [
        {
            "$match": {
                "status": {"$nin": ["cancelled", "returned"]}
            }
        },
        {
            "$group": {
                "_id": "$state",
                "total_orders": {"$sum": 1},
                "total_revenue": {"$sum": "$price"}
            }
        },
        {"$sort": {"total_revenue": -1}}
    ]
    
    result = await db.orders.aggregate(pipeline).to_list(100)
    return result

@router.get("/analytics/sales-by-product")
async def get_sales_by_product(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
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
        {"$limit": 20}
    ]
    
    result = await db.orders.aggregate(pipeline).to_list(20)
    return result
