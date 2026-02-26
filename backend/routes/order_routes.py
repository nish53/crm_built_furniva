from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query
from models import Order, OrderCreate, OrderUpdate, User, OrderStatus, OrderChannel
from auth import get_current_active_user
from database import get_database
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import csv
import io
from dateutil import parser as date_parser

router = APIRouter()

# ... keeping all existing code but updating parse_bool and import functions ...

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
                
                # Check if order already exists
                existing = await db.orders.find_one({"order_number": order_id})
                if existing:
                    skipped_count += 1
                    continue
                
                # Parse dates with dd/mm/yyyy format
                def parse_date(date_str):
                    if not date_str or date_str.strip() == "" or date_str.lower() == 'na':
                        return None
                    try:
                        # Try dd/mm/yyyy format first
                        parts = date_str.strip().split('/')
                        if len(parts) == 3:
                            day, month, year = parts
                            if len(year) == 2:
                                year = '20' + year
                            return datetime(int(year), int(month), int(day), tzinfo=timezone.utc).isoformat()
                        # Fallback to dateparser
                        return date_parser.parse(date_str).replace(tzinfo=timezone.utc).isoformat()
                    except:
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
                
                # Build order object
                order = {
                    "id": str(uuid.uuid4()),
                    "channel": "historical",
                    "order_number": order_id,
                    "order_date": parse_date(row.get("Order Date")) or datetime.now(timezone.utc).isoformat(),
                    "dispatch_by": parse_date(row.get("Dispatch By")),
                    "delivery_by": parse_date(row.get("Delivery By")),
                    "dispatch_date": parse_date(row.get("Actual Dispatch Date")),
                    "delivery_date": parse_date(row.get("Delivery Date")) if status == "delivered" else None,
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
