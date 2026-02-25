from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from models import Order, OrderCreate, OrderUpdate, OrderStatus, OrderChannel, User
from auth import get_current_active_user
from database import get_database
from datetime import datetime, timezone
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
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
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

def parse_amazon_csv(content: str) -> List[dict]:
    reader = csv.DictReader(io.StringIO(content))
    orders = []
    for row in reader:
        try:
            order = {
                "channel": "amazon",
                "order_number": row.get("order-id", row.get("Order ID", "")),
                "order_date": row.get("purchase-date", row.get("Order Date", "")),
                "dispatch_by": row.get("promise-date", row.get("Ship By Date", "")),
                "customer_name": row.get("buyer-name", row.get("Buyer Name", "")),
                "phone": row.get("buyer-phone-number", row.get("Phone", "")),
                "shipping_address": row.get("ship-address-1", row.get("Address", "")),
                "city": row.get("ship-city", row.get("City", "")),
                "state": row.get("ship-state", row.get("State", "")),
                "pincode": row.get("ship-postal-code", row.get("Pincode", "")),
                "sku": row.get("sku", row.get("SKU", "")),
                "asin": row.get("asin", row.get("ASIN", "")),
                "product_name": row.get("product-name", row.get("Product", "")),
                "quantity": int(row.get("quantity-purchased", row.get("Qty", 1))),
                "price": float(row.get("item-price", row.get("Price", 0))),
                "status": "pending"
            }
            orders.append(order)
        except Exception as e:
            continue
    return orders

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
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    content = await file.read()
    content_str = content.decode('utf-8')
    
    if channel.lower() == "amazon":
        orders = parse_amazon_csv(content_str)
    elif channel.lower() == "flipkart":
        orders = parse_flipkart_csv(content_str)
    else:
        raise HTTPException(status_code=400, detail="Invalid channel. Must be 'amazon' or 'flipkart'")
    
    imported_count = 0
    skipped_count = 0
    
    for order_data in orders:
        existing = await db.orders.find_one({"order_number": order_data["order_number"]}, {"_id": 0})
        if existing:
            skipped_count += 1
            continue
        
        try:
            order_data["id"] = str(uuid.uuid4())
            order_data["customer_id"] = str(uuid.uuid4())
            order_data["created_at"] = datetime.now(timezone.utc).isoformat()
            
            if order_data.get("order_date"):
                order_data["order_date"] = date_parser.parse(order_data["order_date"]).isoformat()
            if order_data.get("dispatch_by"):
                order_data["dispatch_by"] = date_parser.parse(order_data["dispatch_by"]).isoformat()
            
            await db.orders.insert_one(order_data)
            imported_count += 1
        except Exception as e:
            skipped_count += 1
            continue
    
    return {
        "message": "CSV import completed",
        "imported": imported_count,
        "skipped": skipped_count,
        "total": len(orders)
    }
