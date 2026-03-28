from fastapi import APIRouter, Depends, HTTPException
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
    
    # PENDING ORDERS = Orders NOT yet dispatched (both pending and confirmed status)
    # These are orders waiting to be shipped
    pending_orders = await db.orders.count_documents({
        "status": {"$in": ["pending", "confirmed"]}
    })
    
    dispatched_today_count = await db.orders.count_documents({
        "dispatch_date": {"$gte": today}
    })
    
    pending_tasks = await db.tasks.count_documents({"status": "pending"})
    
    # PENDING CONFIRMATION = Orders where:
    # 1. Status = "pending" (NOT yet confirmed)
    # 2. dispatch_by is TODAY or PAST (urgent - needs confirmation now)
    # 3. order_conf_calling is NOT true (not yet called/confirmed)
    pending_confirmation = await db.orders.count_documents({
        "status": "pending",
        "dispatch_by": {"$lte": today},
        "$or": [
            {"order_conf_calling": {"$ne": True}},
            {"order_conf_calling": {"$exists": False}}
        ]
    })
    
    low_stock_items = await db.products.count_documents({
        "$expr": {"$lte": ["$stock_quantity", "$reorder_level"]}
    })
    
    pending_claims = await db.claims.count_documents({"status": "filed"})
    
    # Open returns and replacements count
    open_returns = await db.return_requests.count_documents({"return_status": {"$ne": "closed"}})
    open_replacements = await db.replacement_requests.count_documents({"replacement_status": {"$ne": "resolved"}})
    
    # DELAYED ORDERS = Orders that are dispatched but not delivered, and past their delivery_by date
    delayed_orders = await db.orders.count_documents({
        "status": "dispatched",
        "delivery_by": {"$lt": today}
    })
    
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
        pending_calls=pending_confirmation,  # Renamed but keeping field name for compatibility
        low_stock_items=low_stock_items,
        pending_claims=pending_claims,
        revenue_today=revenue_today,
        open_returns=open_returns,
        open_replacements=open_replacements,
        delayed_orders=delayed_orders
    )

@router.get("/recent-orders")
async def get_recent_orders(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    orders = await db.orders.find({}, {"_id": 0}).sort("created_at", -1).limit(10).to_list(10)
    return orders

@router.get("/revenue/{period}")
async def get_revenue_by_period(
    period: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get revenue and units for different time periods"""
    from datetime import timedelta
    
    today = datetime.now(timezone.utc)
    
    # Calculate date range based on period
    if period == "today":
        start_date = today.date().isoformat()
        # Order_date is stored as string in YYYY-MM-DD format
        match_query = {
            "order_date": start_date,  # Exact match for today
            "status": {"$nin": ["cancelled"]}
        }
    elif period == "30days":
        start_date = (today - timedelta(days=30)).date().isoformat()
        match_query = {
            "order_date": {"$gte": start_date},
            "status": {"$nin": ["cancelled"]}
        }
    elif period == "year":
        start_date = today.replace(month=1, day=1).date().isoformat()
        match_query = {
            "order_date": {"$gte": start_date},
            "status": {"$nin": ["cancelled"]}
        }
    else:  # lifetime
        match_query = {
            "status": {"$nin": ["cancelled"]}
        }
    
    # Aggregate revenue and units
    pipeline = [
        {"$match": match_query},
        {
            "$group": {
                "_id": None,
                "amount": {"$sum": "$price"},
                "units": {"$sum": 1}
            }
        }
    ]
    
    result = await db.orders.aggregate(pipeline).to_list(1)
    
    if result:
        return {
            "amount": result[0]["amount"],
            "units": result[0]["units"]
        }
    else:
        return {"amount": 0, "units": 0}

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


@router.get("/priority/dispatch-pending-today")
async def get_dispatch_pending_today(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get orders that need to be dispatched today"""
    today = datetime.now(timezone.utc).date().isoformat()
    
    query = {
        "dispatch_by": today,
        "status": {"$in": ["pending", "confirmed"]},
        "tracking_number": {"$exists": False}  # Not yet shipped
    }
    
    orders = await db.orders.find(query, {"_id": 0}).sort("order_date", -1).to_list(100)
    count = len(orders)
    
    return {
        "count": count,
        "orders": orders,
        "priority": "high",
        "message": f"{count} order(s) need dispatch today"
    }

@router.get("/priority/delayed-orders")
async def get_delayed_orders(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get orders that are delayed (past delivery date but not delivered)"""
    today = datetime.now(timezone.utc).date().isoformat()
    
    query = {
        "delivery_by": {"$lt": today},
        "status": {"$nin": ["delivered", "cancelled", "returned"]},
        "delivered_date": {"$exists": False}
    }
    
    orders = await db.orders.find(query, {"_id": 0}).sort("delivery_by", 1).to_list(100)
    count = len(orders)
    
    return {
        "count": count,
        "orders": orders,
        "priority": "high",
        "message": f"{count} order(s) are delayed"
    }

@router.get("/priority/unmapped-skus")
async def get_unmapped_skus(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get orders with SKUs that haven't been mapped to Master SKU"""
    # Get all unique SKUs from orders
    pipeline = [
        {"$match": {"sku": {"$exists": True, "$ne": ""}}},
        {"$group": {
            "_id": "$sku",
            "channel": {"$first": "$channel"},
            "product_name": {"$first": "$product_name"},
            "count": {"$sum": 1}
        }}
    ]
    
    order_skus = await db.orders.aggregate(pipeline).to_list(1000)
    
    # Get all mapped SKUs from master_sku_mappings
    master_mappings = await db.master_sku_mappings.find({}, {"_id": 0}).to_list(1000)
    
    # Create set of mapped SKUs
    mapped_skus = set()
    for mapping in master_mappings:
        if mapping.get('amazon_sku'):
            mapped_skus.add(mapping['amazon_sku'])
        if mapping.get('flipkart_sku'):
            mapped_skus.add(mapping['flipkart_sku'])
        if mapping.get('website_sku'):
            mapped_skus.add(mapping['website_sku'])
    
    # Find unmapped SKUs
    unmapped = [
        {
            "sku": item["_id"],
            "channel": item["channel"],
            "product_name": item["product_name"],
            "order_count": item["count"]
        }
        for item in order_skus
        if item["_id"] not in mapped_skus
    ]
    
    return {
        "count": len(unmapped),
        "unmapped_skus": unmapped,
        "message": f"{len(unmapped)} SKU(s) need Master SKU assignment"
    }

@router.post("/orders/{order_id}/fake-ship")
async def fake_ship_order(
    order_id: str,
    tracking_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Mark order as fake shipped when customer doesn't respond"""
    result = await db.orders.update_one(
        {"id": order_id},
        {
            "$set": {
                "tracking_number": tracking_id,
                "fake_shipped": True,
                "fake_ship_date": datetime.now(timezone.utc).isoformat(),
                "fake_ship_by": current_user.id,
                "internal_notes": "Fake shipped - customer non-responsive"
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"message": "Order marked as fake shipped", "order_id": order_id}



@router.get("/priority/unspecified-cancellations")
async def get_unspecified_cancellations(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get cancelled orders without cancellation reason - URGENT"""
    query = {
        "status": "cancelled",
        "$or": [
            {"cancellation_reason": {"$exists": False}},
            {"cancellation_reason": None},
            {"cancellation_reason": ""}
        ]
    }
    
    orders = await db.orders.find(query, {"_id": 0}).sort("order_date", -1).to_list(100)
    count = len(orders)
    
    return {
        "count": count,
        "orders": orders,
        "priority": "urgent",
        "message": f"{count} cancelled order(s) need reason specified"
    }

@router.get("/priority/pending-replacements")
async def get_pending_replacements(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get replacement requests that need action"""
    query = {
        "replacement_status": {"$in": ["Replacement Pending", "Priority Review"]}
    }
    
    replacements = await db.replacement_requests.find(query, {"_id": 0}).sort("requested_date", 1).to_list(100)
    count = len(replacements)
    
    return {
        "count": count,
        "replacements": replacements,
        "priority": "high",
        "message": f"{count} replacement(s) need attention"
    }
