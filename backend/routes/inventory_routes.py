"""
Inventory Intelligence Routes - Phase 1
- Bulk CSV Import for SKU Mappings
- Real-Time Stock Buckets
- Inventory Aging Analysis
- Stockout Alerts
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from models import User, MasterSKUMapping
from auth import get_current_active_user
from database import get_database
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict
import uuid
import csv
import io

router = APIRouter(prefix="/inventory", tags=["inventory"])

# ============================================
# BULK CSV IMPORT FOR SKU MAPPINGS
# ============================================

@router.post("/bulk-import-csv")
async def bulk_import_sku_csv(
    file: UploadFile = File(...),
    mode: str = Query("merge", description="merge (skip existing) or replace (update existing)"),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Bulk import Master SKU mappings and Platform Listings from CSV.
    
    Supports MULTIPLE listings per master SKU - just add multiple rows with same master_sku.
    
    Expected CSV columns:
    master_sku, product_name, category, platform, platform_sku, platform_product_id, 
    listing_title, cost_price, selling_price
    
    Example rows:
    FRN-001, Shoe Rack, Storage, amazon, AMZ-001, B08XYZ123, Shoe Rack 3 Tier, 1500, 2999
    FRN-001, Shoe Rack, Storage, amazon, AMZ-002, B09ABC456, Shoe Rack Premium, 1500, 3499
    FRN-001, Shoe Rack, Storage, flipkart, FK-001, FSRACK001, Shoe Rack 3 Tier, 1500, 2899
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    content = await file.read()
    decoded = content.decode('utf-8')
    reader = csv.DictReader(io.StringIO(decoded))
    
    master_skus_created = 0
    master_skus_updated = 0
    listings_created = 0
    listings_skipped = 0
    errors = []
    
    # Track processed master SKUs to avoid duplicates
    processed_master_skus = set()
    
    for row_num, row in enumerate(reader, start=2):
        try:
            master_sku = row.get('master_sku', '').strip()
            product_name = row.get('product_name', '').strip()
            platform = row.get('platform', '').strip().lower()
            
            if not master_sku:
                errors.append({"row": row_num, "error": "master_sku is required"})
                continue
            
            # Create/Update Master SKU (only once per unique master_sku)
            if master_sku not in processed_master_skus:
                if not product_name:
                    errors.append({"row": row_num, "error": "product_name is required for new master_sku"})
                    continue
                
                existing_master = await db.master_sku_mappings.find_one({"master_sku": master_sku})
                
                if existing_master:
                    if mode == "replace":
                        await db.master_sku_mappings.update_one(
                            {"master_sku": master_sku},
                            {"$set": {
                                "product_name": product_name,
                                "category": row.get('category', '').strip() or None,
                                "cost_price": float(row.get('cost_price', 0) or 0) if row.get('cost_price') else None,
                                "selling_price": float(row.get('selling_price', 0) or 0) if row.get('selling_price') else None,
                                "updated_at": datetime.now(timezone.utc).isoformat()
                            }}
                        )
                        master_skus_updated += 1
                else:
                    # Create new master SKU
                    await db.master_sku_mappings.insert_one({
                        "id": str(uuid.uuid4()),
                        "master_sku": master_sku,
                        "product_name": product_name,
                        "category": row.get('category', '').strip() or None,
                        "cost_price": float(row.get('cost_price', 0) or 0) if row.get('cost_price') else None,
                        "selling_price": float(row.get('selling_price', 0) or 0) if row.get('selling_price') else None,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    })
                    master_skus_created += 1
                
                processed_master_skus.add(master_sku)
            
            # Create Platform Listing (if platform specified)
            if platform:
                platform_sku = row.get('platform_sku', '').strip() or None
                platform_product_id = row.get('platform_product_id', '').strip() or None
                listing_title = row.get('listing_title', '').strip() or None
                
                # Check for duplicate listing (same master_sku + platform + platform_sku + platform_product_id)
                existing_listing = await db.platform_listings.find_one({
                    "master_sku": master_sku,
                    "platform": platform,
                    "platform_sku": platform_sku,
                    "platform_product_id": platform_product_id
                })
                
                if existing_listing:
                    if mode == "replace":
                        await db.platform_listings.update_one(
                            {"id": existing_listing["id"]},
                            {"$set": {
                                "listing_title": listing_title,
                                "updated_at": datetime.now(timezone.utc).isoformat()
                            }}
                        )
                    listings_skipped += 1
                else:
                    # Create new listing
                    await db.platform_listings.insert_one({
                        "id": str(uuid.uuid4()),
                        "master_sku": master_sku,
                        "platform": platform,
                        "platform_sku": platform_sku,
                        "platform_product_id": platform_product_id,
                        "listing_title": listing_title,
                        "is_active": True,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    })
                    listings_created += 1
                
        except Exception as e:
            errors.append({"row": row_num, "error": str(e)})
    
    return {
        "success": True,
        "master_skus_created": master_skus_created,
        "master_skus_updated": master_skus_updated,
        "listings_created": listings_created,
        "listings_skipped": listings_skipped,
        "errors": errors[:20],
        "total_errors": len(errors),
        "mode": mode
    }

@router.get("/csv-template")
async def get_csv_template():
    """Get CSV template for bulk SKU import with multiple listings support"""
    return {
        "description": "One master SKU can have MULTIPLE listings. Add multiple rows with same master_sku for different platform listings.",
        "columns": [
            "master_sku", "product_name", "category", 
            "platform", "platform_sku", "platform_product_id", "listing_title",
            "cost_price", "selling_price"
        ],
        "example_rows": [
            {
                "master_sku": "FRN-SR-001",
                "product_name": "Shoe Rack 3 Tier",
                "category": "Storage",
                "platform": "amazon",
                "platform_sku": "AMZ-SR-001",
                "platform_product_id": "B08XYZ123",
                "listing_title": "Shoe Rack 3 Tier - Black",
                "cost_price": "1500",
                "selling_price": "2999"
            },
            {
                "master_sku": "FRN-SR-001",
                "product_name": "Shoe Rack 3 Tier",
                "category": "Storage",
                "platform": "amazon",
                "platform_sku": "AMZ-SR-002",
                "platform_product_id": "B09ABC456",
                "listing_title": "Shoe Rack 3 Tier - White",
                "cost_price": "1500",
                "selling_price": "3199"
            },
            {
                "master_sku": "FRN-SR-001",
                "product_name": "Shoe Rack 3 Tier",
                "category": "Storage",
                "platform": "flipkart",
                "platform_sku": "FK-SR-001",
                "platform_product_id": "FSRACK001",
                "listing_title": "Shoe Rack 3 Tier",
                "cost_price": "1500",
                "selling_price": "2899"
            }
        ],
        "notes": [
            "Same master_sku can appear in multiple rows for different listings",
            "platform: amazon, flipkart, website, meesho, etc.",
            "platform_sku: Your seller SKU on that platform",
            "platform_product_id: ASIN for Amazon, FSN for Flipkart, etc."
        ]
    }


# ============================================
# REAL-TIME STOCK BUCKETS
# ============================================

@router.get("/stock-summary")
async def get_stock_summary(
    master_sku: Optional[str] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Get real-time stock summary with buckets:
    - Reserved (orders placed but not shipped)
    - Available (sellable)
    - Incoming (PO pipeline)
    - Damaged/Blocked (returns pending inspection)
    """
    # Get all SKUs or filter
    sku_query = {}
    if master_sku:
        sku_query["master_sku"] = master_sku
    if category:
        sku_query["category"] = category
    
    skus = await db.master_sku_mappings.find(sku_query, {"_id": 0}).to_list(None)
    
    stock_data = []
    
    for sku in skus:
        sku_id = sku["master_sku"]
        
        # Get procurement total (incoming + received)
        procurement = await db.procurement_batches.aggregate([
            {"$match": {"master_sku": sku_id}},
            {"$group": {"_id": None, "total": {"$sum": "$quantity"}}}
        ]).to_list(1)
        total_procured = procurement[0]["total"] if procurement else 0
        
        # Reserved: Orders placed but not shipped (pending, confirmed, processing)
        reserved = await db.orders.count_documents({
            "master_sku": sku_id,
            "status": {"$in": ["pending", "confirmed", "processing", "ready_to_ship"]}
        })
        
        # Shipped but not delivered (in transit)
        in_transit = await db.orders.count_documents({
            "master_sku": sku_id,
            "status": {"$in": ["dispatched", "in_transit", "out_for_delivery"]}
        })
        
        # Delivered (sold)
        sold = await db.orders.count_documents({
            "master_sku": sku_id,
            "status": {"$in": ["delivered", "completed"]}
        })
        
        # Returns pending inspection (damaged/blocked)
        damaged = await db.return_requests.count_documents({
            "master_sku": sku_id,
            "return_status": {"$in": ["warehouse_received", "condition_checked"]},
            "qc_condition": {"$ne": "mint"}
        })
        
        # Returns in mint condition (can be restocked)
        restockable = await db.return_requests.count_documents({
            "master_sku": sku_id,
            "return_status": "closed",
            "qc_condition": "mint"
        })
        
        # Calculate available
        available = total_procured - reserved - in_transit - sold + restockable - damaged
        if available < 0:
            available = 0
        
        stock_data.append({
            "master_sku": sku_id,
            "product_name": sku.get("product_name", ""),
            "category": sku.get("category", ""),
            "buckets": {
                "total_procured": total_procured,
                "reserved": reserved,
                "in_transit": in_transit,
                "sold": sold,
                "available": available,
                "damaged_blocked": damaged,
                "restockable_returns": restockable
            },
            "sellable": available,
            "atp": available - reserved  # Available to Promise
        })
    
    # Summary totals
    totals = {
        "total_skus": len(stock_data),
        "total_available": sum(s["sellable"] for s in stock_data),
        "total_reserved": sum(s["buckets"]["reserved"] for s in stock_data),
        "total_damaged": sum(s["buckets"]["damaged_blocked"] for s in stock_data)
    }
    
    return {
        "summary": totals,
        "stock_by_sku": stock_data
    }


# ============================================
# INVENTORY AGING ANALYSIS
# ============================================

@router.get("/aging-analysis")
async def get_aging_analysis(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Analyze inventory by age buckets:
    - 0-30 days (Fast Moving)
    - 31-60 days (Normal)
    - 61-90 days (Slow)
    - 91-180 days (Stale)
    - 180+ days (Dead Stock)
    """
    now = datetime.now(timezone.utc)
    
    # Get all SKUs
    sku_query = {}
    if category:
        sku_query["category"] = category
    
    skus = await db.master_sku_mappings.find(sku_query, {"_id": 0}).to_list(None)
    
    aging_data = []
    buckets = {
        "fast_0_30": [],
        "normal_31_60": [],
        "slow_61_90": [],
        "stale_91_180": [],
        "dead_180_plus": []
    }
    
    for sku in skus:
        sku_id = sku["master_sku"]
        
        # Get last sale date
        last_order = await db.orders.find_one(
            {"master_sku": sku_id, "status": {"$in": ["delivered", "completed"]}},
            {"order_date": 1},
            sort=[("order_date", -1)]
        )
        
        # Get procurement date (first batch)
        first_procurement = await db.procurement_batches.find_one(
            {"master_sku": sku_id},
            {"procurement_date": 1},
            sort=[("procurement_date", 1)]
        )
        
        # Calculate days since last sale
        if last_order and last_order.get("order_date"):
            try:
                last_sale = datetime.fromisoformat(str(last_order["order_date"]).replace("Z", "+00:00"))
                days_since_sale = (now - last_sale).days
            except:
                days_since_sale = 999
        else:
            # If no sales, use procurement date
            if first_procurement and first_procurement.get("procurement_date"):
                try:
                    proc_date = datetime.fromisoformat(str(first_procurement["procurement_date"]).replace("Z", "+00:00"))
                    days_since_sale = (now - proc_date).days
                except:
                    days_since_sale = 999
            else:
                days_since_sale = 0  # New SKU
        
        # Get sales velocity (last 30 days)
        thirty_days_ago = (now - timedelta(days=30)).isoformat()
        recent_sales = await db.orders.count_documents({
            "master_sku": sku_id,
            "status": {"$in": ["delivered", "completed"]},
            "order_date": {"$gte": thirty_days_ago}
        })
        
        # Categorize
        if days_since_sale <= 30:
            bucket = "fast_0_30"
            action = "✅ Healthy"
        elif days_since_sale <= 60:
            bucket = "normal_31_60"
            action = "🔵 Monitor"
        elif days_since_sale <= 90:
            bucket = "slow_61_90"
            action = "🟡 Price Review - Consider 10% discount"
        elif days_since_sale <= 180:
            bucket = "stale_91_180"
            action = "🟠 Liquidation Plan - Bundle or clearance sale"
        else:
            bucket = "dead_180_plus"
            action = "🔴 Aggressive Liquidation - Wholesale or deep discount"
        
        sku_aging = {
            "master_sku": sku_id,
            "product_name": sku.get("product_name", ""),
            "category": sku.get("category", ""),
            "days_since_last_sale": days_since_sale,
            "bucket": bucket,
            "sales_last_30_days": recent_sales,
            "suggested_action": action,
            "cost_price": sku.get("cost_price"),
            "selling_price": sku.get("selling_price")
        }
        
        aging_data.append(sku_aging)
        buckets[bucket].append(sku_id)
    
    # Summary
    summary = {
        "total_skus": len(aging_data),
        "fast_moving": len(buckets["fast_0_30"]),
        "normal": len(buckets["normal_31_60"]),
        "slow": len(buckets["slow_61_90"]),
        "stale": len(buckets["stale_91_180"]),
        "dead_stock": len(buckets["dead_180_plus"]),
        "attention_needed": len(buckets["slow_61_90"]) + len(buckets["stale_91_180"]) + len(buckets["dead_180_plus"])
    }
    
    return {
        "summary": summary,
        "aging_by_sku": sorted(aging_data, key=lambda x: -x["days_since_last_sale"]),
        "buckets": buckets
    }


# ============================================
# STOCKOUT ALERTS
# ============================================

@router.get("/stockout-alerts")
async def get_stockout_alerts(
    threshold_days: int = Query(7, description="Alert if stockout in N days"),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Get stockout alerts - SKUs that will run out within threshold days
    
    Formula: Days to Stockout = Available Stock / Avg Daily Sales
    """
    now = datetime.now(timezone.utc)
    thirty_days_ago = (now - timedelta(days=30)).isoformat()
    
    # Get all SKUs
    skus = await db.master_sku_mappings.find({}, {"_id": 0}).to_list(None)
    
    alerts = []
    
    for sku in skus:
        sku_id = sku["master_sku"]
        
        # Get current available stock (simplified)
        procurement = await db.procurement_batches.aggregate([
            {"$match": {"master_sku": sku_id}},
            {"$group": {"_id": None, "total": {"$sum": "$quantity"}}}
        ]).to_list(1)
        total_procured = procurement[0]["total"] if procurement else 0
        
        sold = await db.orders.count_documents({
            "master_sku": sku_id,
            "status": {"$in": ["delivered", "completed", "dispatched", "in_transit"]}
        })
        
        reserved = await db.orders.count_documents({
            "master_sku": sku_id,
            "status": {"$in": ["pending", "confirmed", "processing"]}
        })
        
        available = total_procured - sold - reserved
        if available < 0:
            available = 0
        
        # Calculate avg daily sales (last 30 days)
        recent_sales = await db.orders.count_documents({
            "master_sku": sku_id,
            "status": {"$in": ["delivered", "completed"]},
            "order_date": {"$gte": thirty_days_ago}
        })
        
        avg_daily_sales = recent_sales / 30 if recent_sales > 0 else 0
        
        # Days to stockout
        if avg_daily_sales > 0:
            days_to_stockout = available / avg_daily_sales
        else:
            days_to_stockout = float('inf') if available > 0 else 0
        
        # Alert if stockout within threshold
        if days_to_stockout <= threshold_days:
            priority = "🔴 CRITICAL" if days_to_stockout <= 3 else "🟠 HIGH" if days_to_stockout <= 5 else "🟡 MEDIUM"
            
            # Calculate suggested reorder quantity
            # Formula: (30 day forecast + 7 day buffer) - current stock
            suggested_reorder = max(0, int((avg_daily_sales * 37) - available))
            
            alerts.append({
                "master_sku": sku_id,
                "product_name": sku.get("product_name", ""),
                "category": sku.get("category", ""),
                "current_stock": available,
                "avg_daily_sales": round(avg_daily_sales, 2),
                "days_to_stockout": round(days_to_stockout, 1),
                "priority": priority,
                "suggested_reorder_qty": suggested_reorder,
                "message": f"SKU will stockout in {round(days_to_stockout, 1)} days"
            })
    
    # Sort by urgency
    alerts.sort(key=lambda x: x["days_to_stockout"])
    
    return {
        "threshold_days": threshold_days,
        "total_alerts": len(alerts),
        "critical": len([a for a in alerts if "CRITICAL" in a["priority"]]),
        "high": len([a for a in alerts if "HIGH" in a["priority"]]),
        "medium": len([a for a in alerts if "MEDIUM" in a["priority"]]),
        "alerts": alerts
    }


# ============================================
# INVENTORY DASHBOARD
# ============================================

@router.get("/dashboard")
async def get_inventory_dashboard(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get inventory dashboard with all key metrics"""
    
    # Total SKUs
    total_skus = await db.master_sku_mappings.count_documents({})
    
    # Total procurement value
    procurement_value = await db.procurement_batches.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$total_cost"}}}
    ]).to_list(1)
    total_procurement_value = procurement_value[0]["total"] if procurement_value else 0
    
    # Categories
    categories = await db.master_sku_mappings.distinct("category")
    
    # Get aging summary
    now = datetime.now(timezone.utc)
    
    # Quick aging counts
    dead_stock_count = 0
    stale_count = 0
    
    skus = await db.master_sku_mappings.find({}, {"master_sku": 1}).to_list(None)
    for sku in skus:
        last_order = await db.orders.find_one(
            {"master_sku": sku["master_sku"], "status": {"$in": ["delivered", "completed"]}},
            {"order_date": 1},
            sort=[("order_date", -1)]
        )
        if last_order and last_order.get("order_date"):
            try:
                last_sale = datetime.fromisoformat(str(last_order["order_date"]).replace("Z", "+00:00"))
                days = (now - last_sale).days
                if days > 180:
                    dead_stock_count += 1
                elif days > 90:
                    stale_count += 1
            except:
                pass
    
    # Stockout alerts count
    stockout_data = await get_stockout_alerts(threshold_days=7, current_user=current_user, db=db)
    
    return {
        "total_skus": total_skus,
        "total_procurement_value": total_procurement_value,
        "categories": [c for c in categories if c],
        "category_count": len([c for c in categories if c]),
        "aging": {
            "dead_stock": dead_stock_count,
            "stale_stock": stale_count,
            "attention_needed": dead_stock_count + stale_count
        },
        "stockout_alerts": stockout_data["total_alerts"],
        "critical_stockouts": stockout_data["critical"]
    }


# ============================================
# PHASE 2: DEMAND FORECASTING
# ============================================

@router.get("/demand-forecast")
async def get_demand_forecast(
    master_sku: Optional[str] = None,
    forecast_days: int = Query(30, description="Days to forecast"),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    SKU-level demand forecasting using weighted moving average.
    Includes seasonal multipliers for festive periods.
    """
    now = datetime.now(timezone.utc)
    
    # Seasonal multipliers (India-specific)
    month = now.month
    if month in [10, 11]:  # Diwali season
        seasonal_multiplier = 2.0
        season_name = "Diwali Season"
    elif month == 12 or month == 1:  # New Year
        seasonal_multiplier = 1.5
        season_name = "New Year Season"
    elif month in [4, 5, 6]:  # Summer (furniture slow)
        seasonal_multiplier = 0.8
        season_name = "Summer (Slow)"
    elif month in [7, 8, 9]:  # Monsoon
        seasonal_multiplier = 1.1
        season_name = "Monsoon"
    else:
        seasonal_multiplier = 1.0
        season_name = "Normal"
    
    # Get SKUs
    sku_query = {}
    if master_sku:
        sku_query["master_sku"] = master_sku
    
    skus = await db.master_sku_mappings.find(sku_query, {"_id": 0}).to_list(None)
    
    forecasts = []
    
    for sku in skus:
        sku_id = sku["master_sku"]
        
        # Get historical sales (last 90 days in 3 periods for weighted avg)
        period_sales = []
        for i in range(3):
            start = (now - timedelta(days=30*(i+1))).isoformat()
            end = (now - timedelta(days=30*i)).isoformat()
            
            sales = await db.orders.count_documents({
                "master_sku": sku_id,
                "status": {"$in": ["delivered", "completed"]},
                "order_date": {"$gte": start, "$lt": end}
            })
            period_sales.append(sales)
        
        # Weighted moving average (recent data weighted higher)
        # Weights: [0.5, 0.3, 0.2] for [last 30d, 31-60d, 61-90d]
        if sum(period_sales) > 0:
            weighted_avg = (period_sales[0] * 0.5 + period_sales[1] * 0.3 + period_sales[2] * 0.2)
            daily_avg = weighted_avg / 30
        else:
            daily_avg = 0
        
        # Apply seasonal multiplier
        adjusted_daily = daily_avg * seasonal_multiplier
        
        # Forecast for requested period
        forecast_qty = int(adjusted_daily * forecast_days)
        
        # Get current stock
        procurement = await db.procurement_batches.aggregate([
            {"$match": {"master_sku": sku_id}},
            {"$group": {"_id": None, "total": {"$sum": "$quantity"}}}
        ]).to_list(1)
        total_procured = procurement[0]["total"] if procurement else 0
        
        sold = await db.orders.count_documents({
            "master_sku": sku_id,
            "status": {"$in": ["delivered", "completed", "dispatched", "in_transit"]}
        })
        current_stock = max(0, total_procured - sold)
        
        # Days until stockout
        days_to_stockout = current_stock / adjusted_daily if adjusted_daily > 0 else float('inf')
        
        forecasts.append({
            "master_sku": sku_id,
            "product_name": sku.get("product_name", ""),
            "category": sku.get("category", ""),
            "historical_sales": {
                "last_30_days": period_sales[0],
                "31_60_days": period_sales[1],
                "61_90_days": period_sales[2]
            },
            "daily_avg_base": round(daily_avg, 2),
            "daily_avg_adjusted": round(adjusted_daily, 2),
            "seasonal_multiplier": seasonal_multiplier,
            "forecast_qty": forecast_qty,
            "current_stock": current_stock,
            "days_to_stockout": round(days_to_stockout, 1) if days_to_stockout != float('inf') else "∞",
            "reorder_needed": days_to_stockout < forecast_days
        })
    
    # Sort by reorder urgency
    forecasts.sort(key=lambda x: x["days_to_stockout"] if isinstance(x["days_to_stockout"], (int, float)) else 9999)
    
    return {
        "forecast_period_days": forecast_days,
        "season": season_name,
        "seasonal_multiplier": seasonal_multiplier,
        "total_skus": len(forecasts),
        "skus_needing_reorder": len([f for f in forecasts if f["reorder_needed"]]),
        "forecasts": forecasts
    }


# ============================================
# PHASE 2: PURCHASE INTELLIGENCE
# ============================================

@router.get("/purchase-suggestions")
async def get_purchase_suggestions(
    buffer_days: int = Query(7, description="Buffer stock days"),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Smart purchase order suggestions based on:
    - Forecast demand + buffer - current stock - incoming stock
    """
    now = datetime.now(timezone.utc)
    thirty_days_ago = (now - timedelta(days=30)).isoformat()
    
    skus = await db.master_sku_mappings.find({}, {"_id": 0}).to_list(None)
    
    suggestions = []
    
    for sku in skus:
        sku_id = sku["master_sku"]
        
        # Get 30-day sales
        sales_30d = await db.orders.count_documents({
            "master_sku": sku_id,
            "status": {"$in": ["delivered", "completed"]},
            "order_date": {"$gte": thirty_days_ago}
        })
        
        daily_avg = sales_30d / 30
        
        # Get current stock
        procurement = await db.procurement_batches.aggregate([
            {"$match": {"master_sku": sku_id}},
            {"$group": {"_id": None, "total": {"$sum": "$quantity"}}}
        ]).to_list(1)
        total_procured = procurement[0]["total"] if procurement else 0
        
        sold = await db.orders.count_documents({
            "master_sku": sku_id,
            "status": {"$in": ["delivered", "completed", "dispatched", "in_transit"]}
        })
        reserved = await db.orders.count_documents({
            "master_sku": sku_id,
            "status": {"$in": ["pending", "confirmed", "processing"]}
        })
        
        current_stock = max(0, total_procured - sold - reserved)
        
        # Formula: (30-day forecast + buffer) - current stock
        # Lead time assumed 14 days, so forecast for 44 days (30 + 14)
        lead_time_days = 14
        forecast_period = 30 + lead_time_days
        
        forecast_demand = int(daily_avg * forecast_period)
        buffer_stock = int(daily_avg * buffer_days)
        
        suggested_qty = max(0, forecast_demand + buffer_stock - current_stock)
        
        if suggested_qty > 0:
            # Calculate urgency
            days_to_stockout = current_stock / daily_avg if daily_avg > 0 else 999
            
            if days_to_stockout <= 7:
                urgency = "🔴 URGENT"
            elif days_to_stockout <= 14:
                urgency = "🟠 HIGH"
            elif days_to_stockout <= 21:
                urgency = "🟡 MEDIUM"
            else:
                urgency = "🔵 LOW"
            
            suggestions.append({
                "master_sku": sku_id,
                "product_name": sku.get("product_name", ""),
                "category": sku.get("category", ""),
                "current_stock": current_stock,
                "daily_avg_sales": round(daily_avg, 2),
                "forecast_demand": forecast_demand,
                "buffer_stock": buffer_stock,
                "suggested_order_qty": suggested_qty,
                "days_to_stockout": round(days_to_stockout, 1),
                "urgency": urgency,
                "estimated_cost": suggested_qty * (sku.get("cost_price") or 0),
                "lead_time_days": lead_time_days
            })
    
    # Sort by urgency
    urgency_order = {"🔴 URGENT": 0, "🟠 HIGH": 1, "🟡 MEDIUM": 2, "🔵 LOW": 3}
    suggestions.sort(key=lambda x: (urgency_order.get(x["urgency"], 4), -x["suggested_order_qty"]))
    
    total_cost = sum(s["estimated_cost"] for s in suggestions)
    
    return {
        "buffer_days": buffer_days,
        "lead_time_assumed": 14,
        "total_suggestions": len(suggestions),
        "urgent_count": len([s for s in suggestions if "URGENT" in s["urgency"]]),
        "total_estimated_cost": total_cost,
        "suggestions": suggestions
    }


# ============================================
# PHASE 2: RETURN & DAMAGE INTELLIGENCE
# ============================================

@router.get("/return-analysis")
async def get_return_analysis(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    SKU-level return reason analysis.
    Identifies problematic products and patterns.
    """
    skus = await db.master_sku_mappings.find({}, {"_id": 0}).to_list(None)
    
    analysis = []
    
    for sku in skus:
        sku_id = sku["master_sku"]
        
        # Get total orders
        total_orders = await db.orders.count_documents({
            "master_sku": sku_id,
            "status": {"$in": ["delivered", "completed"]}
        })
        
        if total_orders == 0:
            continue
        
        # Get returns for this SKU
        returns = await db.return_requests.find({
            "master_sku": sku_id
        }, {"_id": 0}).to_list(None)
        
        total_returns = len(returns)
        return_rate = (total_returns / total_orders * 100) if total_orders > 0 else 0
        
        # Analyze return reasons
        reasons = {}
        conditions = {"mint": 0, "damaged": 0, "defective": 0}
        
        for ret in returns:
            reason = ret.get("return_reason") or ret.get("cancellation_reason") or "Unknown"
            reasons[reason] = reasons.get(reason, 0) + 1
            
            condition = ret.get("qc_condition") or ret.get("received_condition")
            if condition in conditions:
                conditions[condition] += 1
        
        # Sort reasons by frequency
        top_reasons = sorted(reasons.items(), key=lambda x: -x[1])[:3]
        
        # Calculate damage rate
        damage_rate = (conditions["damaged"] + conditions["defective"]) / total_returns * 100 if total_returns > 0 else 0
        
        # Flag problematic SKUs
        if return_rate > 10 or damage_rate > 20:
            status = "🔴 PROBLEM"
        elif return_rate > 5 or damage_rate > 10:
            status = "🟡 WATCH"
        else:
            status = "✅ HEALTHY"
        
        analysis.append({
            "master_sku": sku_id,
            "product_name": sku.get("product_name", ""),
            "category": sku.get("category", ""),
            "total_orders": total_orders,
            "total_returns": total_returns,
            "return_rate_percent": round(return_rate, 2),
            "top_return_reasons": [{"reason": r[0], "count": r[1]} for r in top_reasons],
            "condition_breakdown": conditions,
            "damage_rate_percent": round(damage_rate, 2),
            "status": status
        })
    
    # Sort by return rate
    analysis.sort(key=lambda x: -x["return_rate_percent"])
    
    # Summary
    total_returns_all = sum(a["total_returns"] for a in analysis)
    total_orders_all = sum(a["total_orders"] for a in analysis)
    overall_return_rate = (total_returns_all / total_orders_all * 100) if total_orders_all > 0 else 0
    
    return {
        "overall_return_rate": round(overall_return_rate, 2),
        "total_returns": total_returns_all,
        "total_orders": total_orders_all,
        "problem_skus": len([a for a in analysis if "PROBLEM" in a["status"]]),
        "watch_skus": len([a for a in analysis if "WATCH" in a["status"]]),
        "analysis": analysis
    }


@router.get("/courier-damage-analysis")
async def get_courier_damage_analysis(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Courier-wise damage rate analysis.
    Identifies which couriers have highest damage rates.
    """
    # Get all orders with courier info
    orders = await db.orders.find({
        "courier_name": {"$exists": True, "$ne": None}
    }, {"_id": 0, "courier_name": 1, "id": 1}).to_list(None)
    
    courier_stats = {}
    
    for order in orders:
        courier = order.get("courier_name", "Unknown")
        if courier not in courier_stats:
            courier_stats[courier] = {"total": 0, "damaged": 0, "returns": 0}
        courier_stats[courier]["total"] += 1
    
    # Get damage/return info
    returns = await db.return_requests.find({
        "qc_condition": {"$in": ["damaged", "defective"]}
    }, {"_id": 0, "order_id": 1}).to_list(None)
    
    return_order_ids = {r["order_id"] for r in returns}
    
    # Match returns to couriers
    for order in orders:
        courier = order.get("courier_name", "Unknown")
        if order.get("id") in return_order_ids:
            courier_stats[courier]["damaged"] += 1
            courier_stats[courier]["returns"] += 1
    
    # Calculate rates
    courier_analysis = []
    for courier, stats in courier_stats.items():
        damage_rate = (stats["damaged"] / stats["total"] * 100) if stats["total"] > 0 else 0
        
        if damage_rate > 5:
            status = "🔴 HIGH DAMAGE"
        elif damage_rate > 2:
            status = "🟡 MODERATE"
        else:
            status = "✅ GOOD"
        
        courier_analysis.append({
            "courier_name": courier,
            "total_shipments": stats["total"],
            "damaged_shipments": stats["damaged"],
            "damage_rate_percent": round(damage_rate, 2),
            "status": status
        })
    
    courier_analysis.sort(key=lambda x: -x["damage_rate_percent"])
    
    return {
        "total_couriers": len(courier_analysis),
        "high_damage_couriers": len([c for c in courier_analysis if "HIGH" in c["status"]]),
        "analysis": courier_analysis
    }


# ============================================
# PHASE 3: AUTOMATION ENGINE
# ============================================

@router.post("/auto-create-po")
async def auto_create_purchase_order(
    master_sku: str,
    quantity: int,
    supplier_name: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Auto-create a Purchase Order based on intelligent suggestions.
    """
    # Verify SKU exists
    sku = await db.master_sku_mappings.find_one({"master_sku": master_sku})
    if not sku:
        raise HTTPException(status_code=404, detail="Master SKU not found")
    
    po_id = str(uuid.uuid4())
    po_number = f"PO-{datetime.now().strftime('%Y%m%d')}-{po_id[:6].upper()}"
    
    po = {
        "id": po_id,
        "po_number": po_number,
        "master_sku": master_sku,
        "product_name": sku.get("product_name", ""),
        "quantity": quantity,
        "unit_cost": sku.get("cost_price", 0) or 0,
        "total_cost": quantity * (sku.get("cost_price", 0) or 0),
        "supplier_name": supplier_name or "Default Supplier",
        "status": "pending",
        "notes": notes or "Auto-generated by Purchase Intelligence",
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expected_delivery": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()
    }
    
    await db.purchase_orders.insert_one(po)
    
    return {
        "success": True,
        "po_number": po_number,
        "purchase_order": po
    }


@router.get("/purchase-orders")
async def get_purchase_orders(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get all purchase orders"""
    query = {}
    if status:
        query["status"] = status
    
    pos = await db.purchase_orders.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.purchase_orders.count_documents(query)
    
    return {
        "items": pos,
        "total": total
    }


@router.patch("/purchase-orders/{po_id}/status")
async def update_po_status(
    po_id: str,
    status: str,
    received_quantity: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Update purchase order status (pending, confirmed, shipped, received, cancelled)"""
    po = await db.purchase_orders.find_one({"id": po_id})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    update = {
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if status == "received" and received_quantity:
        update["received_quantity"] = received_quantity
        update["received_at"] = datetime.now(timezone.utc).isoformat()
        
        # Create procurement batch entry
        await db.procurement_batches.insert_one({
            "id": str(uuid.uuid4()),
            "master_sku": po["master_sku"],
            "quantity": received_quantity,
            "unit_cost": po.get("unit_cost", 0),
            "total_cost": received_quantity * po.get("unit_cost", 0),
            "supplier": po.get("supplier_name"),
            "po_number": po.get("po_number"),
            "procurement_date": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    await db.purchase_orders.update_one({"id": po_id}, {"$set": update})
    
    return {"success": True, "status": status}


@router.get("/liquidation-suggestions")
async def get_liquidation_suggestions(
    min_age_days: int = Query(90, description="Minimum age for liquidation"),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Get liquidation suggestions for slow/dead stock.
    Suggests price drops, bundling, or clearance actions.
    """
    now = datetime.now(timezone.utc)
    skus = await db.master_sku_mappings.find({}, {"_id": 0}).to_list(None)
    
    suggestions = []
    
    for sku in skus:
        sku_id = sku["master_sku"]
        
        # Get last sale date
        last_order = await db.orders.find_one(
            {"master_sku": sku_id, "status": {"$in": ["delivered", "completed"]}},
            {"order_date": 1},
            sort=[("order_date", -1)]
        )
        
        if last_order and last_order.get("order_date"):
            try:
                last_sale = datetime.fromisoformat(str(last_order["order_date"]).replace("Z", "+00:00"))
                age_days = (now - last_sale).days
            except:
                age_days = 999
        else:
            age_days = 999
        
        if age_days < min_age_days:
            continue
        
        # Get current stock
        procurement = await db.procurement_batches.aggregate([
            {"$match": {"master_sku": sku_id}},
            {"$group": {"_id": None, "total": {"$sum": "$quantity"}}}
        ]).to_list(1)
        total_procured = procurement[0]["total"] if procurement else 0
        
        sold = await db.orders.count_documents({
            "master_sku": sku_id,
            "status": {"$in": ["delivered", "completed", "dispatched"]}
        })
        current_stock = max(0, total_procured - sold)
        
        if current_stock == 0:
            continue
        
        # Calculate suggested discount
        cost_price = sku.get("cost_price", 0) or 0
        selling_price = sku.get("selling_price", 0) or 0
        
        if age_days > 180:
            suggested_discount = 40  # Aggressive
            action = "🔴 LIQUIDATE NOW - Wholesale or 40% off clearance"
            priority = "CRITICAL"
        elif age_days > 120:
            suggested_discount = 25
            action = "🟠 CLEARANCE SALE - 25% off + Bundle offers"
            priority = "HIGH"
        else:
            suggested_discount = 15
            action = "🟡 PRICE DROP - 15% discount recommended"
            priority = "MEDIUM"
        
        suggested_price = selling_price * (1 - suggested_discount/100)
        potential_loss = (cost_price - suggested_price) * current_stock if suggested_price < cost_price else 0
        
        suggestions.append({
            "master_sku": sku_id,
            "product_name": sku.get("product_name", ""),
            "category": sku.get("category", ""),
            "age_days": age_days,
            "current_stock": current_stock,
            "cost_price": cost_price,
            "current_price": selling_price,
            "suggested_discount_percent": suggested_discount,
            "suggested_price": round(suggested_price, 2),
            "potential_loss": round(potential_loss, 2),
            "stock_value": current_stock * cost_price,
            "priority": priority,
            "suggested_action": action
        })
    
    # Sort by age
    suggestions.sort(key=lambda x: -x["age_days"])
    
    total_stock_value = sum(s["stock_value"] for s in suggestions)
    
    return {
        "min_age_days": min_age_days,
        "total_items": len(suggestions),
        "total_stock_value": total_stock_value,
        "critical_count": len([s for s in suggestions if s["priority"] == "CRITICAL"]),
        "high_count": len([s for s in suggestions if s["priority"] == "HIGH"]),
        "suggestions": suggestions
    }


@router.get("/smart-alerts")
async def get_smart_alerts(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Get all smart alerts for inventory management.
    Combines stockout, aging, and return alerts.
    """
    now = datetime.now(timezone.utc)
    thirty_days_ago = (now - timedelta(days=30)).isoformat()
    
    alerts = []
    
    skus = await db.master_sku_mappings.find({}, {"_id": 0}).to_list(None)
    
    for sku in skus:
        sku_id = sku["master_sku"]
        
        # Stock data
        procurement = await db.procurement_batches.aggregate([
            {"$match": {"master_sku": sku_id}},
            {"$group": {"_id": None, "total": {"$sum": "$quantity"}}}
        ]).to_list(1)
        total_procured = procurement[0]["total"] if procurement else 0
        
        sold = await db.orders.count_documents({
            "master_sku": sku_id,
            "status": {"$in": ["delivered", "completed", "dispatched", "in_transit"]}
        })
        reserved = await db.orders.count_documents({
            "master_sku": sku_id,
            "status": {"$in": ["pending", "confirmed", "processing"]}
        })
        current_stock = max(0, total_procured - sold - reserved)
        
        # Sales data
        recent_sales = await db.orders.count_documents({
            "master_sku": sku_id,
            "status": {"$in": ["delivered", "completed"]},
            "order_date": {"$gte": thirty_days_ago}
        })
        daily_avg = recent_sales / 30 if recent_sales > 0 else 0
        
        # ALERT 1: Stockout Warning
        if daily_avg > 0:
            days_to_stockout = current_stock / daily_avg
            if days_to_stockout <= 7:
                alerts.append({
                    "type": "STOCKOUT",
                    "priority": "🔴 CRITICAL" if days_to_stockout <= 3 else "🟠 HIGH",
                    "master_sku": sku_id,
                    "product_name": sku.get("product_name", ""),
                    "message": f"Will stockout in {round(days_to_stockout, 1)} days",
                    "current_stock": current_stock,
                    "daily_avg_sales": round(daily_avg, 2),
                    "action": "Create PO immediately"
                })
        
        # ALERT 2: Dead Stock
        last_order = await db.orders.find_one(
            {"master_sku": sku_id, "status": {"$in": ["delivered", "completed"]}},
            {"order_date": 1},
            sort=[("order_date", -1)]
        )
        
        if last_order and last_order.get("order_date"):
            try:
                last_sale = datetime.fromisoformat(str(last_order["order_date"]).replace("Z", "+00:00"))
                age_days = (now - last_sale).days
                if age_days > 90 and current_stock > 0:
                    alerts.append({
                        "type": "DEAD_STOCK",
                        "priority": "🔴 CRITICAL" if age_days > 180 else "🟠 HIGH" if age_days > 120 else "🟡 MEDIUM",
                        "master_sku": sku_id,
                        "product_name": sku.get("product_name", ""),
                        "message": f"No sales in {age_days} days",
                        "current_stock": current_stock,
                        "age_days": age_days,
                        "action": "Consider liquidation"
                    })
            except:
                pass
        
        # ALERT 3: High Return Rate
        total_orders = await db.orders.count_documents({
            "master_sku": sku_id,
            "status": {"$in": ["delivered", "completed"]}
        })
        total_returns = await db.return_requests.count_documents({"master_sku": sku_id})
        
        if total_orders > 5:  # Minimum sample size
            return_rate = (total_returns / total_orders * 100)
            if return_rate > 10:
                alerts.append({
                    "type": "HIGH_RETURNS",
                    "priority": "🔴 CRITICAL" if return_rate > 20 else "🟠 HIGH",
                    "master_sku": sku_id,
                    "product_name": sku.get("product_name", ""),
                    "message": f"Return rate: {round(return_rate, 1)}%",
                    "total_orders": total_orders,
                    "total_returns": total_returns,
                    "action": "Investigate quality issues"
                })
    
    # Sort by priority
    priority_order = {"🔴 CRITICAL": 0, "🟠 HIGH": 1, "🟡 MEDIUM": 2}
    alerts.sort(key=lambda x: priority_order.get(x["priority"], 3))
    
    return {
        "total_alerts": len(alerts),
        "critical": len([a for a in alerts if "CRITICAL" in a["priority"]]),
        "high": len([a for a in alerts if "HIGH" in a["priority"]]),
        "by_type": {
            "stockout": len([a for a in alerts if a["type"] == "STOCKOUT"]),
            "dead_stock": len([a for a in alerts if a["type"] == "DEAD_STOCK"]),
            "high_returns": len([a for a in alerts if a["type"] == "HIGH_RETURNS"])
        },
        "alerts": alerts
    }


@router.get("/listings-by-sku/{master_sku}")
async def get_listings_by_sku(
    master_sku: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get all platform listings for a master SKU"""
    listings = await db.platform_listings.find(
        {"master_sku": master_sku},
        {"_id": 0}
    ).to_list(None)
    
    # Group by platform
    by_platform = {}
    for listing in listings:
        platform = listing.get("platform", "unknown")
        if platform not in by_platform:
            by_platform[platform] = []
        by_platform[platform].append(listing)
    
    return {
        "master_sku": master_sku,
        "total_listings": len(listings),
        "platforms": list(by_platform.keys()),
        "by_platform": by_platform,
        "listings": listings
    }


# ============================================
# PHASE 4: MULTI-WAREHOUSE & AUDIT CONTROL
# ============================================

# --- WAREHOUSE MANAGEMENT ---

@router.post("/warehouses")
async def create_warehouse(
    name: str,
    code: str,
    address: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    pincode: Optional[str] = None,
    is_active: bool = True,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Create a new warehouse"""
    existing = await db.warehouses.find_one({"code": code})
    if existing:
        raise HTTPException(status_code=400, detail="Warehouse code already exists")
    
    warehouse = {
        "id": str(uuid.uuid4()),
        "name": name,
        "code": code.upper(),
        "address": address,
        "city": city,
        "state": state,
        "pincode": pincode,
        "is_active": is_active,
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.warehouses.insert_one(warehouse)
    
    # Return warehouse without MongoDB _id
    return {
        "id": warehouse["id"],
        "name": warehouse["name"],
        "code": warehouse["code"],
        "address": warehouse["address"],
        "city": warehouse["city"],
        "state": warehouse["state"],
        "pincode": warehouse["pincode"],
        "is_active": warehouse["is_active"],
        "created_by": warehouse["created_by"],
        "created_at": warehouse["created_at"]
    }


@router.get("/warehouses")
async def get_warehouses(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get all warehouses"""
    warehouses = await db.warehouses.find({}, {"_id": 0}).to_list(None)
    return {"warehouses": warehouses, "total": len(warehouses)}


@router.get("/warehouse-stock/{warehouse_code}")
async def get_warehouse_stock(
    warehouse_code: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get stock levels for a specific warehouse"""
    warehouse = await db.warehouses.find_one({"code": warehouse_code.upper()}, {"_id": 0})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Get all stock entries for this warehouse
    stock = await db.warehouse_stock.find(
        {"warehouse_code": warehouse_code.upper()},
        {"_id": 0}
    ).to_list(None)
    
    # Enrich with product names
    for item in stock:
        sku = await db.master_sku_mappings.find_one(
            {"master_sku": item["master_sku"]},
            {"product_name": 1}
        )
        item["product_name"] = sku.get("product_name", "") if sku else ""
    
    total_units = sum(s.get("quantity", 0) for s in stock)
    
    return {
        "warehouse": warehouse,
        "stock": stock,
        "total_skus": len(stock),
        "total_units": total_units
    }


# --- STOCK ADJUSTMENTS ---

@router.post("/stock-adjustment")
async def create_stock_adjustment(
    master_sku: str,
    warehouse_code: str,
    adjustment_type: str,  # "add", "remove", "set"
    quantity: int,
    reason: str,
    reference: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Create a stock adjustment with audit trail.
    Types: add (increase), remove (decrease), set (override)
    """
    # Verify SKU exists
    sku = await db.master_sku_mappings.find_one({"master_sku": master_sku})
    if not sku:
        raise HTTPException(status_code=404, detail="Master SKU not found")
    
    # Get current stock
    current = await db.warehouse_stock.find_one({
        "master_sku": master_sku,
        "warehouse_code": warehouse_code.upper()
    })
    current_qty = current.get("quantity", 0) if current else 0
    
    # Calculate new quantity
    if adjustment_type == "add":
        new_qty = current_qty + quantity
    elif adjustment_type == "remove":
        new_qty = max(0, current_qty - quantity)
    elif adjustment_type == "set":
        new_qty = quantity
    else:
        raise HTTPException(status_code=400, detail="Invalid adjustment_type")
    
    # Create adjustment record (audit)
    adjustment = {
        "id": str(uuid.uuid4()),
        "master_sku": master_sku,
        "warehouse_code": warehouse_code.upper(),
        "adjustment_type": adjustment_type,
        "quantity_change": quantity if adjustment_type == "add" else -quantity if adjustment_type == "remove" else new_qty - current_qty,
        "quantity_before": current_qty,
        "quantity_after": new_qty,
        "reason": reason,
        "reference": reference,
        "created_by": current_user.id,
        "created_by_name": current_user.name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.stock_adjustments.insert_one(adjustment)
    
    # Update warehouse stock
    if current:
        await db.warehouse_stock.update_one(
            {"master_sku": master_sku, "warehouse_code": warehouse_code.upper()},
            {"$set": {"quantity": new_qty, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        await db.warehouse_stock.insert_one({
            "id": str(uuid.uuid4()),
            "master_sku": master_sku,
            "warehouse_code": warehouse_code.upper(),
            "quantity": new_qty,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Return adjustment without MongoDB _id
    return {
        "success": True,
        "adjustment": {
            "id": adjustment["id"],
            "master_sku": adjustment["master_sku"],
            "warehouse_code": adjustment["warehouse_code"],
            "adjustment_type": adjustment["adjustment_type"],
            "quantity_change": adjustment["quantity_change"],
            "quantity_before": adjustment["quantity_before"],
            "quantity_after": adjustment["quantity_after"],
            "reason": adjustment["reason"],
            "reference": adjustment["reference"],
            "created_by": adjustment["created_by"],
            "created_by_name": adjustment["created_by_name"],
            "created_at": adjustment["created_at"]
        }
    }


@router.get("/stock-adjustments")
async def get_stock_adjustments(
    master_sku: Optional[str] = None,
    warehouse_code: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get stock adjustment history (audit log)"""
    query = {}
    if master_sku:
        query["master_sku"] = master_sku
    if warehouse_code:
        query["warehouse_code"] = warehouse_code.upper()
    
    adjustments = await db.stock_adjustments.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.stock_adjustments.count_documents(query)
    
    return {"items": adjustments, "total": total}


# --- CYCLE COUNTS ---

@router.post("/cycle-count")
async def create_cycle_count(
    warehouse_code: str,
    sku_count: int = Query(10, description="Number of SKUs to count"),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Create a new cycle count with randomly selected SKUs.
    """
    import random
    
    # Get all SKUs with stock in this warehouse
    stock_items = await db.warehouse_stock.find(
        {"warehouse_code": warehouse_code.upper(), "quantity": {"$gt": 0}},
        {"master_sku": 1, "quantity": 1}
    ).to_list(None)
    
    if not stock_items:
        raise HTTPException(status_code=400, detail="No stock items in warehouse")
    
    # Random selection
    selected = random.sample(stock_items, min(sku_count, len(stock_items)))
    
    # Create cycle count
    count_id = str(uuid.uuid4())
    count_number = f"CC-{datetime.now().strftime('%Y%m%d')}-{count_id[:6].upper()}"
    
    items = []
    for item in selected:
        sku = await db.master_sku_mappings.find_one({"master_sku": item["master_sku"]})
        items.append({
            "master_sku": item["master_sku"],
            "product_name": sku.get("product_name", "") if sku else "",
            "system_qty": item["quantity"],
            "counted_qty": None,
            "variance": None,
            "counted": False
        })
    
    cycle_count = {
        "id": count_id,
        "count_number": count_number,
        "warehouse_code": warehouse_code.upper(),
        "status": "pending",
        "items": items,
        "total_items": len(items),
        "counted_items": 0,
        "total_variance": 0,
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.cycle_counts.insert_one(cycle_count)
    
    return cycle_count


@router.get("/cycle-counts")
async def get_cycle_counts(
    warehouse_code: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get cycle count history"""
    query = {}
    if warehouse_code:
        query["warehouse_code"] = warehouse_code.upper()
    if status:
        query["status"] = status
    
    counts = await db.cycle_counts.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.cycle_counts.count_documents(query)
    
    return {"items": counts, "total": total}


@router.patch("/cycle-count/{count_id}/item")
async def update_cycle_count_item(
    count_id: str,
    master_sku: str,
    counted_qty: int,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Update counted quantity for a cycle count item"""
    cycle_count = await db.cycle_counts.find_one({"id": count_id})
    if not cycle_count:
        raise HTTPException(status_code=404, detail="Cycle count not found")
    
    # Find and update the item
    items = cycle_count["items"]
    item_found = False
    counted_items = 0
    total_variance = 0
    
    for item in items:
        if item["master_sku"] == master_sku:
            item["counted_qty"] = counted_qty
            item["variance"] = counted_qty - item["system_qty"]
            item["counted"] = True
            item["counted_by"] = current_user.id
            item["counted_at"] = datetime.now(timezone.utc).isoformat()
            item_found = True
        
        if item["counted"]:
            counted_items += 1
            total_variance += abs(item.get("variance", 0))
    
    if not item_found:
        raise HTTPException(status_code=404, detail="SKU not in this cycle count")
    
    # Update cycle count
    status = "completed" if counted_items == len(items) else "in_progress"
    
    await db.cycle_counts.update_one(
        {"id": count_id},
        {"$set": {
            "items": items,
            "counted_items": counted_items,
            "total_variance": total_variance,
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"success": True, "counted_items": counted_items, "status": status}


# --- SHRINKAGE DETECTION ---

@router.get("/shrinkage-report")
async def get_shrinkage_report(
    warehouse_code: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Detect shrinkage by comparing expected vs actual stock.
    Expected = Opening + Received - Sold - Returns - Damaged
    """
    query = {}
    if warehouse_code:
        query["warehouse_code"] = warehouse_code.upper()
    
    # Get all SKUs
    skus = await db.master_sku_mappings.find({}, {"_id": 0, "master_sku": 1, "product_name": 1}).to_list(None)
    
    shrinkage_items = []
    
    for sku in skus:
        sku_id = sku["master_sku"]
        
        # Get actual stock (from warehouse_stock or calculated)
        if warehouse_code:
            actual = await db.warehouse_stock.find_one({
                "master_sku": sku_id,
                "warehouse_code": warehouse_code.upper()
            })
            actual_qty = actual.get("quantity", 0) if actual else 0
        else:
            # Sum across all warehouses
            actual_sum = await db.warehouse_stock.aggregate([
                {"$match": {"master_sku": sku_id}},
                {"$group": {"_id": None, "total": {"$sum": "$quantity"}}}
            ]).to_list(1)
            actual_qty = actual_sum[0]["total"] if actual_sum else 0
        
        # Calculate expected stock
        # Received (procurement)
        procurement = await db.procurement_batches.aggregate([
            {"$match": {"master_sku": sku_id}},
            {"$group": {"_id": None, "total": {"$sum": "$quantity"}}}
        ]).to_list(1)
        received = procurement[0]["total"] if procurement else 0
        
        # Sold (completed orders)
        sold = await db.orders.count_documents({
            "master_sku": sku_id,
            "status": {"$in": ["delivered", "completed"]}
        })
        
        # In transit (not yet delivered)
        in_transit = await db.orders.count_documents({
            "master_sku": sku_id,
            "status": {"$in": ["dispatched", "in_transit", "out_for_delivery"]}
        })
        
        # Reserved (pending orders)
        reserved = await db.orders.count_documents({
            "master_sku": sku_id,
            "status": {"$in": ["pending", "confirmed", "processing"]}
        })
        
        expected_qty = received - sold - in_transit - reserved
        
        # Calculate shrinkage
        shrinkage = expected_qty - actual_qty
        shrinkage_percent = (shrinkage / expected_qty * 100) if expected_qty > 0 else 0
        
        if abs(shrinkage) > 0:
            status = "🔴 HIGH" if abs(shrinkage_percent) > 5 else "🟡 MEDIUM" if abs(shrinkage_percent) > 2 else "🔵 LOW"
            
            shrinkage_items.append({
                "master_sku": sku_id,
                "product_name": sku.get("product_name", ""),
                "expected_qty": expected_qty,
                "actual_qty": actual_qty,
                "shrinkage_qty": shrinkage,
                "shrinkage_percent": round(shrinkage_percent, 2),
                "status": status,
                "breakdown": {
                    "received": received,
                    "sold": sold,
                    "in_transit": in_transit,
                    "reserved": reserved
                }
            })
    
    # Sort by shrinkage amount
    shrinkage_items.sort(key=lambda x: -abs(x["shrinkage_qty"]))
    
    total_shrinkage = sum(s["shrinkage_qty"] for s in shrinkage_items)
    high_shrinkage_count = len([s for s in shrinkage_items if "HIGH" in s["status"]])
    
    return {
        "warehouse_code": warehouse_code or "ALL",
        "total_skus_with_variance": len(shrinkage_items),
        "total_shrinkage_units": total_shrinkage,
        "high_shrinkage_count": high_shrinkage_count,
        "items": shrinkage_items
    }


# --- AUDIT TRAIL ---

@router.get("/audit-log")
async def get_audit_log(
    entity_type: Optional[str] = None,  # "stock_adjustment", "cycle_count", "po", etc.
    master_sku: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get comprehensive audit log of all inventory movements"""
    logs = []
    
    # Stock adjustments
    if not entity_type or entity_type == "stock_adjustment":
        query = {}
        if master_sku:
            query["master_sku"] = master_sku
        if user_id:
            query["created_by"] = user_id
        if start_date:
            query["created_at"] = {"$gte": start_date}
        if end_date:
            query.setdefault("created_at", {})["$lte"] = end_date
        
        adjustments = await db.stock_adjustments.find(query, {"_id": 0}).to_list(None)
        for adj in adjustments:
            logs.append({
                "type": "ADJUSTMENT",
                "entity_id": adj["id"],
                "master_sku": adj["master_sku"],
                "action": adj["adjustment_type"],
                "quantity_change": adj["quantity_change"],
                "reason": adj["reason"],
                "user_id": adj["created_by"],
                "user_name": adj.get("created_by_name", ""),
                "timestamp": adj["created_at"]
            })
    
    # Cycle counts
    if not entity_type or entity_type == "cycle_count":
        query = {}
        if start_date:
            query["created_at"] = {"$gte": start_date}
        
        counts = await db.cycle_counts.find(query, {"_id": 0}).to_list(None)
        for cc in counts:
            variance_items = [i for i in cc.get("items", []) if i.get("variance", 0) != 0]
            logs.append({
                "type": "CYCLE_COUNT",
                "entity_id": cc["id"],
                "reference": cc["count_number"],
                "warehouse": cc["warehouse_code"],
                "action": cc["status"],
                "items_counted": cc.get("counted_items", 0),
                "total_variance": cc.get("total_variance", 0),
                "user_id": cc["created_by"],
                "timestamp": cc["created_at"]
            })
    
    # Purchase orders received
    if not entity_type or entity_type == "po":
        query = {"status": "received"}
        if master_sku:
            query["master_sku"] = master_sku
        
        pos = await db.purchase_orders.find(query, {"_id": 0}).to_list(None)
        for po in pos:
            logs.append({
                "type": "PO_RECEIVED",
                "entity_id": po["id"],
                "reference": po["po_number"],
                "master_sku": po["master_sku"],
                "action": "received",
                "quantity_change": po.get("received_quantity", po["quantity"]),
                "user_id": po["created_by"],
                "timestamp": po.get("received_at", po["created_at"])
            })
    
    # Sort by timestamp
    logs.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Paginate
    total = len(logs)
    logs = logs[skip:skip+limit]
    
    return {
        "items": logs,
        "total": total
    }

