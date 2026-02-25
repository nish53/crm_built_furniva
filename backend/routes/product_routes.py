from fastapi import APIRouter, Depends, HTTPException
from models import Product, ProductCreate, User
from auth import get_current_active_user
from database import get_database
from datetime import datetime, timezone
from typing import List
import uuid

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/", response_model=Product)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    existing = await db.products.find_one({"sku": product_data.sku}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")
    
    product_dict = product_data.model_dump()
    product_dict["id"] = str(uuid.uuid4())
    product_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.products.insert_one(product_dict)
    return Product(**product_dict)

@router.get("/", response_model=List[Product])
async def get_products(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    products = await db.products.find({}, {"_id": 0}).sort("name", 1).to_list(1000)
    return products

@router.get("/{product_id}", response_model=Product)
async def get_product(
    product_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**product)

@router.patch("/{product_id}")
async def update_product(
    product_id: str,
    update_data: dict,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.products.update_one(
        {"id": product_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    return Product(**product)

@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}
