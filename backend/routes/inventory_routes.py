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
    Bulk import Master SKU mappings from CSV.
    
    Expected CSV columns:
    master_sku, product_name, category, amazon_sku, amazon_asin, amazon_fnsku, 
    flipkart_sku, flipkart_fsn, website_sku, cost_price, selling_price
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    content = await file.read()
    decoded = content.decode('utf-8')
    reader = csv.DictReader(io.StringIO(decoded))
    
    imported = 0
    updated = 0
    skipped = 0
    errors = []
    
    for row_num, row in enumerate(reader, start=2):  # Start from 2 (header is row 1)
        try:
            master_sku = row.get('master_sku', '').strip()
            product_name = row.get('product_name', '').strip()
            
            if not master_sku:
                errors.append({"row": row_num, "error": "master_sku is required"})
                continue
            
            if not product_name:
                errors.append({"row": row_num, "error": "product_name is required"})
                continue
            
            # Build mapping dict
            mapping_dict = {
                "master_sku": master_sku,
                "product_name": product_name,
                "category": row.get('category', '').strip() or None,
                "amazon_sku": row.get('amazon_sku', '').strip() or None,
                "amazon_asin": row.get('amazon_asin', '').strip() or None,
                "amazon_fnsku": row.get('amazon_fnsku', '').strip() or None,
                "flipkart_sku": row.get('flipkart_sku', '').strip() or None,
                "flipkart_fsn": row.get('flipkart_fsn', '').strip() or None,
                "website_sku": row.get('website_sku', '').strip() or None,
                "cost_price": float(row.get('cost_price', 0) or 0) if row.get('cost_price') else None,
                "selling_price": float(row.get('selling_price', 0) or 0) if row.get('selling_price') else None,
            }
            
            # Check if exists
            existing = await db.master_sku_mappings.find_one({"master_sku": master_sku})
            
            if existing:
                if mode == "replace":
                    mapping_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
                    await db.master_sku_mappings.update_one(
                        {"master_sku": master_sku},
                        {"$set": mapping_dict}
                    )
                    updated += 1
                else:
                    skipped += 1
            else:
                mapping_dict["id"] = str(uuid.uuid4())
                mapping_dict["created_at"] = datetime.now(timezone.utc).isoformat()
                await db.master_sku_mappings.insert_one(mapping_dict)
                
                # Auto-create platform listings
                await _create_platform_listings(db, mapping_dict)
                imported += 1
                
        except Exception as e:
            errors.append({"row": row_num, "error": str(e)})
    
    return {
        "success": True,
        "imported": imported,
        "updated": updated,
        "skipped": skipped,
        "errors": errors[:20],  # Limit errors shown
        "total_errors": len(errors),
        "mode": mode
    }

async def _create_platform_listings(db, mapping: dict):
    """Helper to create platform listings from mapping"""
    master_sku = mapping["master_sku"]
    
    # Amazon
    if mapping.get("amazon_sku") or mapping.get("amazon_asin"):
        listing = {
            "id": str(uuid.uuid4()),
            "master_sku": master_sku,
            "platform": "amazon",
            "platform_sku": mapping.get("amazon_sku") or "",
            "platform_product_id": mapping.get("amazon_asin") or "",
            "platform_fnsku": mapping.get("amazon_fnsku") or "",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.platform_listings.insert_one(listing)
    
    # Flipkart
    if mapping.get("flipkart_sku") or mapping.get("flipkart_fsn"):
        listing = {
            "id": str(uuid.uuid4()),
            "master_sku": master_sku,
            "platform": "flipkart",
            "platform_sku": mapping.get("flipkart_sku") or "",
            "platform_product_id": mapping.get("flipkart_fsn") or "",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.platform_listings.insert_one(listing)
    
    # Website
    if mapping.get("website_sku"):
        listing = {
            "id": str(uuid.uuid4()),
            "master_sku": master_sku,
            "platform": "website",
            "platform_sku": mapping.get("website_sku") or "",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.platform_listings.insert_one(listing)

@router.get("/csv-template")
async def get_csv_template():
    """Get CSV template for bulk SKU import"""
    return {
        "columns": [
            "master_sku", "product_name", "category", 
            "amazon_sku", "amazon_asin", "amazon_fnsku",
            "flipkart_sku", "flipkart_fsn", "website_sku",
            "cost_price", "selling_price"
        ],
        "example_row": {
            "master_sku": "FRN-SR-001",
            "product_name": "Shoe Rack 3 Tier",
            "category": "Storage",
            "amazon_sku": "SR-AMZ-001",
            "amazon_asin": "B08XYZ123",
            "amazon_fnsku": "X001ABC",
            "flipkart_sku": "SR-FK-001",
            "flipkart_fsn": "FKSRACK001",
            "website_sku": "SR-WEB-001",
            "cost_price": "1500",
            "selling_price": "2999"
        }
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
