from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks
from models import Order, OrderCreate, OrderUpdate, OrderStatus, OrderChannel, User
from auth import get_current_active_user
from database import get_database
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import uuid
import csv
import io
from dateutil import parser as date_parser

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/", response_model=Order)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    order_dict = order_data.model_dump()
    order_dict["id"] = str(uuid.uuid4())
    order_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    order_dict["order_date"] = order_dict["order_date"].isoformat()
    
    if order_dict.get("dispatch_by"):
        order_dict["dispatch_by"] = order_dict["dispatch_by"].isoformat()
    
    if order_dict.get("delivery_by"):
        order_dict["delivery_by"] = order_dict["delivery_by"].isoformat()
    
    await db.orders.insert_one(order_dict)
    return Order(**order_dict)

@router.get("/", response_model=List[Order])
async def get_orders(
    status: Optional[OrderStatus] = None,
    channel: Optional[OrderChannel] = None,
    pincode: Optional[str] = None,
    state: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    query = {}
    
    if status:
        query["status"] = status
    if channel:
        query["channel"] = channel
    if pincode:
        query["pincode"] = pincode
    if state:
        query["state"] = state
    if start_date:
        query["order_date"] = {"$gte": start_date}
    if end_date:
        if "order_date" not in query:
            query["order_date"] = {}
        query["order_date"]["$lte"] = end_date
    if search:
        query["$or"] = [
            {"order_number": {"$regex": search, "$options": "i"}},
            {"customer_name": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}},
            {"tracking_number": {"$regex": search, "$options": "i"}}
        ]
    
    orders = await db.orders.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return orders

@router.get("/{order_id}", response_model=Order)
async def get_order(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return Order(**order)

@router.patch("/{order_id}", response_model=Order)
async def update_order(
    order_id: str,
    update_data: OrderUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    # Get old order status before update
    old_order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not old_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    old_status = old_order.get("status")
    
    update_dict = {k: v for k, v in update_data.model_dump(exclude_unset=True).items() if v is not None}
    
    if not update_dict:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    for key, value in update_dict.items():
        if isinstance(value, datetime):
            update_dict[key] = value.isoformat()
    
    result = await db.orders.update_one(
        {"id": order_id},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Trigger automation if status changed
    new_status = update_dict.get("status")
    if new_status and new_status != old_status:
        from automation_service import automation_service
        background_tasks.add_task(
            automation_service.process_order_status_change,
            order_id,
            old_status,
            new_status,
            db
        )
    
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    return Order(**order)

@router.delete("/{order_id}")
async def delete_order(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
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
    """Bulk delete multiple orders"""
    if not order_ids:
        raise HTTPException(status_code=400, detail="No order IDs provided")
    
    result = await db.orders.delete_many({"id": {"$in": order_ids}})
    return {
        "message": f"Successfully deleted {result.deleted_count} orders",
        "deleted_count": result.deleted_count
    }

@router.post("/bulk-update")
async def bulk_update_orders(
    order_ids: List[str],
    update_fields: dict,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Bulk update multiple orders with same field values"""
    if not order_ids:
        raise HTTPException(status_code=400, detail="No order IDs provided")
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No update fields provided")
    
    # Convert datetime fields if present
    for key, value in update_fields.items():
        if isinstance(value, str) and 'date' in key.lower():
            try:
                update_fields[key] = datetime.fromisoformat(value.replace('Z', '+00:00')).isoformat()
            except:
                pass
    
    result = await db.orders.update_many(
        {"id": {"$in": order_ids}},
        {"$set": update_fields}
    )
    
    return {
        "message": f"Successfully updated {result.modified_count} orders",
        "modified_count": result.modified_count,
        "matched_count": result.matched_count
    }


def parse_amazon_csv(content: str, delimiter: str = ',') -> List[dict]:
    """Parse Amazon order file (CSV or tab-separated TXT)
    
    Supports both Amazon CSV format and tab-separated TXT format.
    Handles all standard Amazon order report fields.
    """
    try:
        reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
        orders = []
        
        for row in reader:
            try:
                # Skip empty rows
                if not row or not any(row.values()):
                    continue
                
                # Extract order details with comprehensive field mapping
                amazon_order_id = row.get("amazon-order-id", "")
                merchant_order_id = row.get("merchant-order-id", "")
                order_number = amazon_order_id or merchant_order_id or row.get("Order ID", "")
                
                # Skip if no order number
                if not order_number:
                    continue
                
                # Parse quantity - handle empty strings and cancelled orders
                quantity_str = row.get("quantity", row.get("quantity-purchased", row.get("Qty", "1")))
                try:
                    quantity = int(float(quantity_str)) if quantity_str and quantity_str.strip() else 0
                except (ValueError, AttributeError):
                    quantity = 0
                
                # Skip cancelled orders with 0 quantity
                if quantity == 0:
                    continue
                
                # Parse price
                price_str = row.get("item-price", row.get("Price", "0"))
                try:
                    price = float(price_str) if price_str and price_str.strip() else 0.0
                except (ValueError, AttributeError):
                    price = 0.0
                
                # Map order status
                order_status = row.get("order-status", "").lower()
                item_status = row.get("item-status", "").lower()
                
                if order_status == "cancelled" or item_status == "cancelled":
                    status = "cancelled"
                elif order_status == "shipped" or item_status == "shipped":
                    status = "dispatched"
                elif order_status == "pending" or item_status == "unshipped":
                    status = "pending"
                else:
                    status = "pending"
                
                # Build order object with all fields
                order = {
                    "channel": "amazon",
                    "order_number": order_number,
                    "order_date": row.get("purchase-date", row.get("Order Date", "")),
                    "last_updated": row.get("last-updated-date", ""),
                    "dispatch_by": row.get("latest-ship-date", row.get("promise-date", row.get("Ship By Date", ""))),
                    "customer_name": row.get("buyer-name", row.get("Buyer Name", row.get("recipient-name", "Customer"))),
                    "phone": row.get("buyer-phone-number", row.get("Phone", "")),
                    "shipping_address": row.get("ship-address-1", row.get("Address", "")),
                    "city": row.get("ship-city", row.get("City", "")),
                    "state": row.get("ship-state", row.get("State", "")),
                    "pincode": row.get("ship-postal-code", row.get("Pincode", "")),
                    "country": row.get("ship-country", "IN"),
                    "sku": row.get("sku", row.get("SKU", "")),
                    "asin": row.get("asin", row.get("ASIN", "")),
                    "product_name": row.get("product-name", row.get("Product", "")),
                    "quantity": quantity,
                    "price": price,
                    "currency": row.get("currency", "INR"),
                    "fulfillment_channel": row.get("fulfillment-channel", ""),
                    "sales_channel": row.get("sales-channel", ""),
                    "ship_service_level": row.get("ship-service-level", ""),
                    "item_tax": row.get("item-tax", "0"),
                    "shipping_price": row.get("shipping-price", "0"),
                    "shipping_tax": row.get("shipping-tax", "0"),
                    "status": status,
                    "notes": f"Imported from Amazon on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
                
                orders.append(order)
                
            except Exception as e:
                # Log error but continue processing other orders
                print(f"Error parsing row: {e}")
                continue
        
        return orders
        
    except Exception as e:
        print(f"Error reading CSV/TXT file: {e}")
        return []

def parse_flipkart_csv(content: str) -> List[dict]:
    reader = csv.DictReader(io.StringIO(content))
    orders = []
    for row in reader:
        try:
            order = {
                "channel": "flipkart",
                "order_number": row.get("Order ID", row.get("order_id", "")),
                "order_date": row.get("Order Date", row.get("order_date", "")),
                "dispatch_by": row.get("Dispatch By Date", row.get("dispatch_by", "")),
                "customer_name": row.get("Customer Name", row.get("customer_name", "")),
                "phone": row.get("Phone", row.get("phone", "")),
                "shipping_address": row.get("Shipping Address", row.get("address", "")),
                "city": row.get("City", row.get("city", "")),
                "state": row.get("State", row.get("state", "")),
                "pincode": row.get("Pincode", row.get("pincode", "")),
                "sku": row.get("SKU", row.get("sku", "")),
                "product_name": row.get("Product Title", row.get("product", "")),
                "quantity": int(row.get("Quantity", row.get("qty", 1))),
                "price": float(row.get("Selling Price", row.get("price", 0))),
                "status": "pending"
            }
            orders.append(order)
        except Exception as e:
            continue
    return orders

@router.post("/import-csv")
async def import_csv(
    file: UploadFile = File(...),
    channel: str = Query(..., description="amazon or flipkart"),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Import orders from CSV or TXT file
    
    Supports:
    - Amazon: .csv (comma-separated) or .txt (tab-separated)
    - Flipkart: .csv (comma-separated)
    
    Automatically skips:
    - Duplicate orders (same order number)
    - Cancelled orders (quantity = 0)
    - Invalid rows
    """
    filename = file.filename.lower()
    if not filename.endswith('.csv') and not filename.endswith('.txt'):
        raise HTTPException(
            status_code=400, 
            detail="File must be a CSV or TXT file. Amazon supports both .csv and .txt formats."
        )
    
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
            raise HTTPException(
                status_code=400,
                detail="Unable to decode file. Please ensure it's a valid text file."
            )
        
        # Validate file has content
        if not content_str.strip():
            raise HTTPException(status_code=400, detail="File is empty")
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    # Parse orders based on channel
    if channel.lower() == "amazon":
        # Detect delimiter - tab for .txt files, comma for .csv
        delimiter = '\t' if filename.endswith('.txt') else ','
        orders = parse_amazon_csv(content_str, delimiter=delimiter)
    elif channel.lower() == "flipkart":
        orders = parse_flipkart_csv(content_str)
    else:
        raise HTTPException(status_code=400, detail="Invalid channel. Must be 'amazon' or 'flipkart'")
    
    if not orders:
        raise HTTPException(
            status_code=400,
            detail="No valid orders found in file. Please check the file format and ensure it contains order data."
        )
    
    imported_count = 0
    skipped_count = 0
    error_count = 0
    
    for order_data in orders:
        # Check for duplicates
        existing = await db.orders.find_one({"order_number": order_data["order_number"]}, {"_id": 0})
        if existing:
            skipped_count += 1
            continue
        
        try:
            order_data["id"] = str(uuid.uuid4())
            order_data["customer_id"] = str(uuid.uuid4())
            order_data["created_at"] = datetime.now(timezone.utc).isoformat()
            
            # Parse dates with error handling
            if order_data.get("order_date"):
                try:
                    order_data["order_date"] = date_parser.parse(order_data["order_date"]).isoformat()
                except Exception:
                    order_data["order_date"] = datetime.now(timezone.utc).isoformat()
            else:
                order_data["order_date"] = datetime.now(timezone.utc).isoformat()
            
            # Handle dispatch_by - remove empty strings and set to None
            dispatch_by_val = order_data.get("dispatch_by", "").strip()
            if dispatch_by_val:
                try:
                    order_data["dispatch_by"] = date_parser.parse(dispatch_by_val).isoformat()
                except Exception:
                    # Set dispatch date to 3 days from order date
                    order_date = date_parser.parse(order_data["order_date"]) if order_data.get("order_date") else datetime.now(timezone.utc)
                    order_data["dispatch_by"] = (order_date + timedelta(days=3)).isoformat()
            else:
                # Remove empty string or set to None - Pydantic will handle it
                order_data.pop("dispatch_by", None)
            
            # Handle delivery_by similarly
            delivery_by_val = order_data.get("delivery_by", "").strip()
            if delivery_by_val:
                try:
                    order_data["delivery_by"] = date_parser.parse(delivery_by_val).isoformat()
                except Exception:
                    order_data.pop("delivery_by", None)
            else:
                order_data.pop("delivery_by", None)
            
            await db.orders.insert_one(order_data)
            imported_count += 1
            
        except Exception as e:
            error_count += 1
            print(f"Error importing order {order_data.get('order_number')}: {e}")
            continue
    
    return {
        "success": True,
        "message": f"Import completed successfully. Imported {imported_count} orders.",
        "imported": imported_count,
        "skipped": skipped_count,
        "errors": error_count,
        "total_processed": len(orders),
        "details": {
            "file_name": file.filename,
            "channel": channel,
            "file_type": "tab-separated" if filename.endswith('.txt') else "comma-separated"
        }
    }

@router.post("/import-historical")
async def import_historical_orders(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Import historical orders with comprehensive status data
    
    Expected headers:
    Order ID, Order Date, Dispatch By, Delivery By, Actual Dispatch Date,
    Order Conf Calling, Assembly Type, Dispatch Confirmation Sent,
    Did Not Pick Day 1, Confirmed on Day 1?, Did Not Pick Day 2, Confirmed on Day 2?,
    Did Not Pick Day 3, Confirmed on Day 3?, Deliver Conf, Review Conf,
    Delivery Date, Customer Name, Billing No., Shipping No., Place, State,
    Pincode, SKU, Qty, Tracking, Actual Shipping Company, Instructions,
    Live Status, Price, Pickup Status, Reason for Cancellation/Replacement
    """
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
                
                # Parse dates
                def parse_date(date_str):
                    if not date_str or date_str.strip() == "":
                        return None
                    try:
                        return date_parser.parse(date_str).isoformat()
                    except:
                        return None
                
                # Map status
                live_status = row.get("Live Status", "").lower()
                status_mapping = {
                    "delivered": "delivered",
                    "in transit": "dispatched",
                    "returned": "returned",
                    "cancelled": "cancelled",
                    "damaged": "returned",
                    "lost": "cancelled",
                    "replaced": "replacement"
                }
                status = status_mapping.get(live_status, "delivered")
                
                # Build order object
                order = {
                    "id": str(uuid.uuid4()),
                    "channel": "historical",
                    "order_number": order_id,
                    "order_date": parse_date(row.get("Order Date")) or datetime.now(timezone.utc).isoformat(),
                    "dispatch_by": parse_date(row.get("Dispatch By")),
                    "delivery_by": parse_date(row.get("Delivery By")),
                    "dispatch_date": parse_date(row.get("Actual Dispatch Date")),
                    "delivery_date": parse_date(row.get("Delivery Date")),
                    "customer_id": str(uuid.uuid4()),
                    "customer_name": row.get("Customer Name", "Unknown"),
                    "phone": row.get("Billing No.", row.get("Shipping No.", "")),
                    "phone_secondary": row.get("Shipping No.") if row.get("Shipping No.") != row.get("Billing No.") else None,
                    "city": row.get("Place", ""),
                    "state": row.get("State", ""),
                    "pincode": row.get("Pincode", ""),
                    "sku": row.get("SKU", ""),
                    "product_name": row.get("SKU", "Product"),
                    "quantity": int(float(row.get("Qty", "1") or "1")),
                    "price": float(row.get("Price", "0") or "0"),
                    "status": status,
                    "tracking_number": row.get("Tracking", ""),
                    "courier_partner": row.get("Actual Shipping Company", ""),
                    "instructions": row.get("Instructions", ""),
                    "assembly_type": row.get("Assembly Type", ""),
                    "dc1_called": row.get("Order Conf Calling", "").lower() in ["yes", "done", "completed"],
                    "cp_sent": row.get("Dispatch Confirmation Sent", "").lower() in ["yes", "done", "sent"],
                    "dnp1_conf": row.get("Did Not Pick Day 1", "").lower() in ["yes", "true"],
                    "dnp2_conf": row.get("Did Not Pick Day 2", "").lower() in ["yes", "true"],
                    "dnp3_conf": row.get("Did Not Pick Day 3", "").lower() in ["yes", "true"],
                    "deliver_conf": row.get("Deliver Conf", "").lower() in ["yes", "done", "sent"],
                    "review_conf": row.get("Review Conf", "").lower() in ["yes", "done", "sent"],
                    "pickup_status": row.get("Pickup Status", ""),
                    "cancellation_reason": row.get("Reason for Cancellation/Replacement", ""),
                    "internal_notes": f"Imported from historical data. Original status: {live_status}",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "is_historical": True
                }
                
                await db.orders.insert_one(order)
                imported_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f"Row {row_num}: {str(e)}")
                if len(errors) <= 10:  # Only store first 10 errors
                    continue
        
        return {
            "imported": imported_count,
            "skipped": skipped_count,
            "errors": error_count,
            "error_details": errors[:10] if errors else []
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

                except Exception:
                    order_data["order_date"] = datetime.now(timezone.utc).isoformat()
            else:
                order_data["order_date"] = datetime.now(timezone.utc).isoformat()
            
            # Handle dispatch_by - remove empty strings and set to None
            dispatch_by_val = order_data.get("dispatch_by", "").strip()
            if dispatch_by_val:
                try:
                    order_data["dispatch_by"] = date_parser.parse(dispatch_by_val).isoformat()
                except Exception:
                    # Set dispatch date to 3 days from order date
                    order_date = date_parser.parse(order_data["order_date"]) if order_data.get("order_date") else datetime.now(timezone.utc)
                    order_data["dispatch_by"] = (order_date + timedelta(days=3)).isoformat()
            else:
                # Remove empty string or set to None - Pydantic will handle it
                order_data.pop("dispatch_by", None)
            
            # Handle delivery_by similarly
            delivery_by_val = order_data.get("delivery_by", "").strip()
            if delivery_by_val:
                try:
                    order_data["delivery_by"] = date_parser.parse(delivery_by_val).isoformat()
                except Exception:
                    order_data.pop("delivery_by", None)
            else:
                order_data.pop("delivery_by", None)
            
            await db.orders.insert_one(order_data)
            imported_count += 1
            
        except Exception as e:
            error_count += 1
            print(f"Error importing order {order_data.get('order_number')}: {e}")
            continue
    
    return {
        "success": True,
        "message": f"Import completed successfully. Imported {imported_count} orders.",
        "imported": imported_count,
        "skipped": skipped_count,
        "errors": error_count,
        "total_processed": len(orders),
        "details": {
            "file_name": file.filename,
            "channel": channel,
            "file_type": "tab-separated" if filename.endswith('.txt') else "comma-separated"
        }
    }
