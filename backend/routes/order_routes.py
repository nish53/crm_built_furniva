from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query
from models import Order, OrderCreate, OrderUpdate, User, OrderStatus, OrderChannel, PaginatedResponse
from auth import get_current_active_user
from database import get_database
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import csv
import io
import math
from dateutil import parser as date_parser
from routes.edit_history_routes import track_order_changes

router = APIRouter(prefix="/orders", tags=["orders"])

# ===== ORDER CRUD ENDPOINTS =====

@router.get("/", response_model=PaginatedResponse[Order])
async def get_orders(
    status: Optional[str] = None,
    channel: Optional[str] = None,
    search: Optional[str] = None,
    master_sku: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get orders with optional filters and pagination"""
    query = {}
    
    if status:
        query["status"] = status
    if channel:
        query["channel"] = channel
    if master_sku:
        query["master_sku"] = master_sku
    if city:
        query["city"] = {"$regex": city, "$options": "i"}
    if state:
        query["state"] = {"$regex": state, "$options": "i"}
    
    if search:
        query["$or"] = [
            {"order_number": {"$regex": search, "$options": "i"}},
            {"customer_name": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}},
            {"tracking_number": {"$regex": search, "$options": "i"}},
        ]
    
    if min_price is not None or max_price is not None:
        price_query = {}
        if min_price is not None:
            price_query["$gte"] = min_price
        if max_price is not None:
            price_query["$lte"] = max_price
        query["price"] = price_query
    
    # Get total count for pagination
    total = await db.orders.count_documents(query)
    
    # Get paginated results
    orders = await db.orders.find(query, {"_id": 0}).sort("order_date", -1).skip(skip).limit(limit).to_list(limit)
    
    # Calculate pagination metadata
    page = (skip // limit) + 1 if limit > 0 else 1
    total_pages = math.ceil(total / limit) if limit > 0 else 1
    
    return {
        "items": orders,
        "total": total,
        "page": page,
        "page_size": limit,
        "total_pages": total_pages
    }

@router.get("/{order_id}", response_model=Order)
async def get_order(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get a single order by ID"""
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.post("/", response_model=Order)
async def create_order(
    order: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Create a new order"""
    order_dict = order.model_dump()
    order_dict["id"] = str(uuid.uuid4())
    order_dict["customer_id"] = str(uuid.uuid4())
    order_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    
    # Ensure order_date is set
    if not order_dict.get("order_date"):
        order_dict["order_date"] = datetime.now(timezone.utc).isoformat()
    
    await db.orders.insert_one(order_dict)
    return Order(**order_dict)

@router.patch("/{order_id}", response_model=Order)
async def update_order(
    order_id: str,
    order_update: OrderUpdate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Update an existing order with edit history tracking"""
    existing = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Only update provided fields
    update_data = order_update.model_dump(exclude_unset=True)
    
    # Validate cancellation_reason is required when status is cancelled
    if update_data.get("status") == "cancelled":
        if not update_data.get("cancellation_reason") and not existing.get("cancellation_reason"):
            raise HTTPException(
                status_code=400, 
                detail="Cancellation reason is required when changing status to cancelled"
            )
    
    if update_data:
        # Track previous status for undo functionality
        if "status" in update_data and update_data["status"] != existing.get("status"):
            update_data["previous_status"] = existing.get("status")
        
        # Track changes before updating
        await track_order_changes(
            order_id=order_id,
            old_order=existing,
            new_data=update_data,
            user_email=current_user.email,
            edit_reason=update_data.get("internal_notes"),  # Use notes as edit reason if provided
            db=db
        )
        
        # Update last_updated timestamp
        update_data["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        await db.orders.update_one({"id": order_id}, {"$set": update_data})
    
    updated_order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    return Order(**updated_order)

@router.patch("/{order_id}/undo-status")
async def undo_order_status(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Undo the last status change on an order"""
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    previous_status = order.get("previous_status")
    if not previous_status:
        raise HTTPException(status_code=400, detail="No previous status to revert to")
    
    # Track the change
    await track_order_changes(
        order_id=order_id,
        old_order=order,
        new_data={"status": previous_status},
        user_email=current_user.email,
        edit_reason="Status undo",
        db=db
    )
    
    # Revert to previous status
    await db.orders.update_one(
        {"id": order_id},
        {"$set": {
            "status": previous_status,
            "previous_status": None,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    updated_order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    return {
        "message": f"Status reverted to {previous_status}",
        "order": Order(**updated_order)
    }

@router.patch("/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    cancellation_reason: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Cancel an order (pre-dispatch only) with mandatory reason"""
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Only allow cancellation for pre-dispatch orders
    current_status = order.get("status", "")
    if current_status not in ["pending", "confirmed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel order with status '{current_status}'. Only pending or confirmed orders can be cancelled."
        )
    
    if not cancellation_reason or not cancellation_reason.strip():
        raise HTTPException(status_code=400, detail="Cancellation reason is required")
    
    # Track the change
    await track_order_changes(
        order_id=order_id,
        old_order=order,
        new_data={"status": "cancelled", "cancellation_reason": cancellation_reason},
        user_email=current_user.email,
        edit_reason=f"Order cancelled: {cancellation_reason}",
        db=db
    )
    
    # Cancel the order
    await db.orders.update_one(
        {"id": order_id},
        {"$set": {
            "status": "cancelled",
            "previous_status": current_status,
            "cancellation_reason": cancellation_reason,
            "cancelled_at": datetime.now(timezone.utc).isoformat(),
            "cancelled_by": current_user.email,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    updated_order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    return {
        "message": "Order cancelled successfully",
        "order": Order(**updated_order)
    }

@router.delete("/{order_id}")
async def delete_order(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Delete an order"""
    result = await db.orders.delete_one({"id": order_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Order deleted successfully"}

@router.post("/bulk-delete")
async def bulk_delete_orders(
    order_ids: List[str],
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Delete multiple orders"""
    if not order_ids:
        raise HTTPException(status_code=400, detail="No order IDs provided")
    
    result = await db.orders.delete_many({"id": {"$in": order_ids}})
    return {
        "message": f"Successfully deleted {result.deleted_count} order(s)",
        "deleted_count": result.deleted_count
    }

@router.post("/bulk-update")
async def bulk_update_orders(
    request_data: dict,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Update multiple orders with the same status"""
    order_ids = request_data.get("order_ids", [])
    status = request_data.get("status")
    
    if not order_ids:
        raise HTTPException(status_code=400, detail="No order IDs provided")
    
    update_data = {}
    if status:
        update_data["status"] = status
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    result = await db.orders.update_many(
        {"id": {"$in": order_ids}},
        {"$set": update_data}
    )
    
    return {
        "message": f"Successfully updated {result.modified_count} order(s)",
        "modified_count": result.modified_count
    }

@router.post("/bulk-update-channel")
async def bulk_update_channel(
    request_data: dict,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Update channel for multiple orders"""
    order_ids = request_data.get("order_ids", [])
    channel = request_data.get("channel", "")
    
    if not order_ids:
        raise HTTPException(status_code=400, detail="No order IDs provided")
    if not channel:
        raise HTTPException(status_code=400, detail="Channel is required")
    
    result = await db.orders.update_many(
        {"id": {"$in": order_ids}},
        {"$set": {"channel": channel}}
    )
    
    return {
        "message": f"Successfully updated channel for {result.modified_count} order(s)",
        "modified_count": result.modified_count
    }

# ===== HISTORICAL IMPORT ENDPOINT =====

@router.post("/import-historical")
async def import_historical_orders(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Import historical orders with comprehensive status data - supports multi-item orders"""
    filename = file.filename.lower()
    if not filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")
    
    try:
        content = await file.read()
        
        # Try multiple encodings
        content_str = None
        for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1']:
            try:
                content_str = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if not content_str:
            raise HTTPException(status_code=400, detail="Unable to decode file")
        
        # Parse CSV
        reader = csv.DictReader(io.StringIO(content_str))
        imported_count = 0
        skipped_count = 0
        error_count = 0
        errors = []
        
        for row_num, row in enumerate(reader, start=2):
            try:
                # Skip empty rows
                if not row or not any(row.values()):
                    skipped_count += 1
                    continue
                
                # Parse order data
                order_id = row.get("Order ID", "").strip()
                if not order_id:
                    skipped_count += 1
                    continue
                
                # For multi-item orders: Don't skip, create separate records per item
                # Each item gets unique id but same order_number
                # This allows multiple items under same order while maintaining current schema
                
                # Parse dates with dd/mm/yyyy or dd/mm/yyyy HH:MM format
                def parse_date(date_str):
                    if not date_str or date_str.strip() == "" or date_str.lower() == 'na':
                        return None
                    try:
                        date_str = date_str.strip()
                        
                        # Try dd/mm/yyyy HH:MM format first (with time)
                        if ' ' in date_str:
                            date_part = date_str.split(' ')[0]  # Get just the date part
                            parts = date_part.split('/')
                            if len(parts) == 3:
                                day, month, year = parts
                                if len(year) == 2:
                                    year = '20' + year
                                return datetime(int(year), int(month), int(day), tzinfo=timezone.utc).isoformat()
                        
                        # Try dd/mm/yyyy format (without time)
                        parts = date_str.split('/')
                        if len(parts) == 3:
                            day, month, year = parts
                            if len(year) == 2:
                                year = '20' + year
                            return datetime(int(year), int(month), int(day), tzinfo=timezone.utc).isoformat()
                        
                        # Fallback to dateparser for other formats
                        return date_parser.parse(date_str).replace(tzinfo=timezone.utc).isoformat()
                    except Exception:
                        return None
                
                # Map status - handle "Pickup Pending" correctly
                live_status = row.get("Live Status", "").lower().strip()
                pickup_status = row.get("Pickup Status", "").lower().strip()
                
                status_mapping = {
                    "delivered": "delivered",
                    "in transit": "dispatched",
                    "returned": "returned",
                    "cancelled": "cancelled",
                    "damaged": "returned",
                    "lost": "cancelled",
                    "replaced": "replacement"
                }
                
                # Handle pickup pending specifically
                if "pickup pending" in live_status or "pickup pending" in pickup_status:
                    status = "pending"
                else:
                    status = status_mapping.get(live_status, "delivered")
                
                # Parse boolean fields - handle TRUE/FALSE strings
                def parse_bool(value):
                    if not value:
                        return False
                    val = str(value).upper().strip()
                    return val in ['YES', 'DONE', 'COMPLETED', 'TRUE', '1', 'SENT']
                
                # Parse SKU and quantity for multi-item support
                sku_value = row.get("SKU", "")
                qty_value = row.get("Qty", "1")
                price_value = row.get("Price", "0")
                
                # Parse order date - skip row if invalid
                order_date = parse_date(row.get("Order Date"))
                if not order_date:
                    error_msg = f"Row {row_num}: Invalid or missing Order Date"
                    errors.append(error_msg)
                    error_count += 1
                    continue
                
                # Build order object
                order = {
                    "id": str(uuid.uuid4()),
                    "channel": "historical",
                    "order_number": order_id,
                    "order_date": order_date,
                    "dispatch_by": parse_date(row.get("Dispatch By")),
                    "delivery_by": parse_date(row.get("Delivery By")),
                    "dispatch_date": parse_date(row.get("Actual Dispatch Date")),
                    "delivery_date": parse_date(row.get("Delivery Date")),  # Import delivery date regardless of status
                    "customer_id": str(uuid.uuid4()),
                    "customer_name": row.get("Customer Name", "Unknown"),
                    "phone": row.get("Billing No.", row.get("Shipping No.", "")).strip(),
                    "phone_secondary": row.get("Shipping No.", "").strip() if row.get("Shipping No.") != row.get("Billing No.") else None,
                    "city": row.get("Place", ""),
                    "state": row.get("State", ""),
                    "pincode": row.get("Pincode", ""),
                    "sku": sku_value,
                    "product_name": sku_value if sku_value else "Product",
                    "quantity": int(float(qty_value or "1")),
                    "price": float(price_value or "0"),
                    "status": status,
                    "tracking_number": row.get("Tracking", ""),
                    "courier_partner": row.get("Actual Shipping Company", ""),
                    "instructions": row.get("Instructions", ""),
                    
                    # Historical calling/confirmation data
                    "assembly_type": row.get("Assembly Type", "").strip(),
                    "paid_assembly": row.get("Assembly Type", "").strip().lower() == "paid",  # Set boolean based on assembly type
                    "order_conf_calling": parse_bool(row.get("Order Conf Calling")),
                    "dispatch_conf_sent": parse_bool(row.get("Dispatch Confirmation Sent")),
                    "dnp_day1": parse_bool(row.get("Did Not Pick Day 1")),
                    "confirmed_day1": parse_bool(row.get("Confirmed on Day 1?")),
                    "dnp_day2": parse_bool(row.get("Did Not Pick Day 2")),
                    "confirmed_day2": parse_bool(row.get("Confirmed on Day 2?")),
                    "dnp_day3": parse_bool(row.get("Did Not Pick Day 3")),
                    "confirmed_day3": parse_bool(row.get("Confirmed on Day 3?")),
                    "deliver_conf": parse_bool(row.get("Deliver Conf")),
                    "review_conf": parse_bool(row.get("Review Conf")),
                    
                    "pickup_status": pickup_status,
                    "cancellation_reason": row.get("Reason for Cancellation/Replacement", ""),
                    "internal_notes": f"Imported from historical data. Original status: {live_status}",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "is_historical": True
                }
                
                await db.orders.insert_one(order)
                imported_count += 1
                
            except Exception as e:
                error_count += 1
                error_msg = f"Row {row_num}: {str(e)}"
                errors.append(error_msg)
                # Continue processing other rows
        
        return {
            "imported": imported_count,
            "skipped": skipped_count,
            "errors": error_count,
            "error_details": errors,
            "message": f"Import completed: {imported_count} imported, {skipped_count} skipped, {error_count} errors"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
