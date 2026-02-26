from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from models import ImportMappingTemplate, ImportMappingTemplateCreate, User, Order
from auth import get_current_active_user
from database import get_database
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import uuid
import csv
import io
from dateutil import parser as date_parser

router = APIRouter(prefix="/import", tags=["import"])

@router.post("/preview-file")
async def preview_import_file(
    file: UploadFile = File(...),
    delimiter: str = Query(",", description="Delimiter character"),
    has_header: bool = Query(True, description="File has header row"),
    current_user: User = Depends(get_current_active_user)
):
    """Preview file contents and detect columns for mapping"""
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
        
        # Auto-detect delimiter if tab
        if '\t' in content_str and ',' not in content_str.split('\n')[0]:
            delimiter = '\t'
        
        reader = csv.reader(io.StringIO(content_str), delimiter=delimiter)
        rows = list(reader)
        
        if not rows:
            raise HTTPException(status_code=400, detail="File is empty")
        
        headers = rows[0] if has_header else [f"Column {i+1}" for i in range(len(rows[0]))]
        preview_rows = rows[1:6] if has_header else rows[:5]
        
        return {
            "filename": file.filename,
            "delimiter": delimiter,
            "has_header": has_header,
            "columns": headers,
            "preview_data": preview_rows,
            "total_rows": len(rows) - (1 if has_header else 0),
            "detected_delimiter": delimiter
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@router.get("/available-fields")
async def get_available_import_fields(
    current_user: User = Depends(get_current_active_user)
):
    """Get list of available system fields for mapping"""
    return {
        "required_fields": [
            {"field": "order_number", "type": "string", "description": "Unique order identifier"},
            {"field": "order_date", "type": "datetime", "description": "Order date"},
            {"field": "customer_name", "type": "string", "description": "Customer name"},
            {"field": "phone", "type": "string", "description": "Phone number"},
            {"field": "pincode", "type": "string", "description": "PIN code"},
            {"field": "sku", "type": "string", "description": "Product SKU"},
            {"field": "product_name", "type": "string", "description": "Product name"},
            {"field": "quantity", "type": "integer", "description": "Quantity"},
            {"field": "price", "type": "float", "description": "Price"}
        ],
        "optional_fields": [
            {"field": "master_sku", "type": "string", "description": "Master SKU (unified across platforms)"},
            {"field": "asin", "type": "string", "description": "Amazon ASIN"},
            {"field": "fnsku", "type": "string", "description": "Amazon FNSKU"},
            {"field": "fsn_id", "type": "string", "description": "Flipkart FSN ID"},
            {"field": "dispatch_by", "type": "datetime", "description": "Dispatch deadline"},
            {"field": "delivery_by", "type": "datetime", "description": "Delivery deadline"},
            {"field": "phone_secondary", "type": "string", "description": "Secondary phone"},
            {"field": "email", "type": "string", "description": "Email address"},
            {"field": "billing_address", "type": "string", "description": "Billing address"},
            {"field": "shipping_address", "type": "string", "description": "Full shipping address"},
            {"field": "shipping_address_line1", "type": "string", "description": "Address line 1"},
            {"field": "shipping_address_line2", "type": "string", "description": "Address line 2"},
            {"field": "landmark", "type": "string", "description": "Landmark"},
            {"field": "city", "type": "string", "description": "City"},
            {"field": "state", "type": "string", "description": "State"},
            {"field": "country", "type": "string", "description": "Country"},
            {"field": "tracking_number", "type": "string", "description": "Tracking number"},
            {"field": "courier_partner", "type": "string", "description": "Courier name"},
            {"field": "item_tax", "type": "float", "description": "Item tax amount"},
            {"field": "shipping_price", "type": "float", "description": "Shipping price"},
            {"field": "shipping_tax", "type": "float", "description": "Shipping tax"},
            {"field": "total_amount", "type": "float", "description": "Total order amount"},
            {"field": "fulfillment_channel", "type": "string", "description": "Fulfillment channel (FBA, FBM, etc.)"},
            {"field": "sales_channel", "type": "string", "description": "Sales channel"},
            {"field": "ship_service_level", "type": "string", "description": "Shipping service level"},
            {"field": "payment_method", "type": "string", "description": "Payment method"},
            {"field": "is_business_order", "type": "boolean", "description": "Business order flag"},
            {"field": "is_prime", "type": "boolean", "description": "Prime order flag"},
            {"field": "gift_message", "type": "string", "description": "Gift message"},
            {"field": "instructions", "type": "string", "description": "Special instructions"}
        ]
    }

@router.post("/with-mapping")
async def import_with_column_mapping(
    file: UploadFile = File(...),
    channel: str = Query(..., description="Channel name (amazon, flipkart, website, etc.)"),
    column_mappings: str = Query(..., description="JSON string of column mappings"),
    delimiter: str = Query(",", description="Single character delimiter"),
    has_header: bool = Query(True, description="File has header row"),
    auto_lookup_master_sku: bool = Query(True, description="Auto-lookup Master SKU from platform SKU"),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Import orders using custom column mapping"""
    import json
    
    try:
        mappings = json.loads(column_mappings)
    except:
        raise HTTPException(status_code=400, detail="Invalid column_mappings JSON")
    
    # Fix delimiter - handle escape sequences
    if delimiter == "\\t" or delimiter == "\t":
        delimiter = '\t'
    elif len(delimiter) != 1:
        raise HTTPException(status_code=400, detail="Delimiter must be a single character")
    
    try:
        content = await file.read()
        content_str = None
        for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1']:
            try:
                content_str = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if not content_str:
            raise HTTPException(status_code=400, detail="Unable to decode file")
        
        reader = csv.DictReader(io.StringIO(content_str), delimiter=delimiter)
        
        imported_count = 0
        skipped_count = 0
        error_count = 0
        errors = []
        
        for row in reader:
            try:
                # Map columns to system fields
                order_data = {"channel": channel}
                
                for csv_column, system_field in mappings.items():
                    if system_field and csv_column in row:
                        value = row[csv_column].strip() if row[csv_column] else None
                        if value:
                            order_data[system_field] = value
                
                # Skip if no order_number
                if not order_data.get("order_number"):
                    skipped_count += 1
                    continue
                
                # Check for duplicates
                existing = await db.orders.find_one({"order_number": order_data["order_number"]}, {"_id": 0})
                if existing:
                    skipped_count += 1
                    continue
                
                # Parse quantity
                try:
                    quantity = int(float(order_data.get("quantity", 1)))
                    if quantity == 0:
                        skipped_count += 1
                        continue
                    order_data["quantity"] = quantity
                except:
                    order_data["quantity"] = 1
                
                # Parse price
                try:
                    order_data["price"] = float(order_data.get("price", 0))
                except:
                    order_data["price"] = 0.0
                
                # Auto-lookup Master SKU if enabled
                if auto_lookup_master_sku and order_data.get("sku") and not order_data.get("master_sku"):
                    # Look up in platform_listings collection by SKU
                    listing = await db.platform_listings.find_one(
                        {"platform_sku": order_data["sku"]},
                        {"_id": 0}
                    )
                    if listing:
                        order_data["master_sku"] = listing["master_sku"]
                
                # Add required fields
                order_data["id"] = str(uuid.uuid4())
                order_data["customer_id"] = str(uuid.uuid4())
                order_data["created_at"] = datetime.now(timezone.utc).isoformat()
                
                # Parse dates
                if order_data.get("order_date"):
                    try:
                        order_data["order_date"] = date_parser.parse(order_data["order_date"]).isoformat()
                    except:
                        order_data["order_date"] = datetime.now(timezone.utc).isoformat()
                else:
                    order_data["order_date"] = datetime.now(timezone.utc).isoformat()
                
                if order_data.get("dispatch_by"):
                    try:
                        order_data["dispatch_by"] = date_parser.parse(order_data["dispatch_by"]).isoformat()
                    except:
                        order_data.pop("dispatch_by", None)
                
                # Set defaults
                order_data.setdefault("status", "pending")
                order_data.setdefault("customer_name", "Unknown")
                order_data.setdefault("phone", "")
                order_data.setdefault("pincode", "")
                order_data.setdefault("product_name", "")
                
                await db.orders.insert_one(order_data)
                imported_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append({"row": row.get("order_number", "unknown"), "error": str(e)})
        
        return {
            "success": True,
            "message": f"Import completed. Imported {imported_count} orders.",
            "imported": imported_count,
            "skipped": skipped_count,
            "errors": error_count,
            "error_details": errors[:10],
            "filename": file.filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

# Import Template Management
@router.post("/templates", response_model=ImportMappingTemplate)
async def create_import_template(
    template: ImportMappingTemplateCreate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Create an import mapping template"""
    template_dict = template.model_dump()
    template_dict["id"] = str(uuid.uuid4())
    template_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    template_dict["created_by"] = current_user.id
    
    await db.import_mapping_templates.insert_one(template_dict)
    return ImportMappingTemplate(**template_dict)

@router.get("/templates", response_model=List[ImportMappingTemplate])
async def get_import_templates(
    channel: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get all import templates"""
    query = {}
    if channel:
        query["channel"] = channel
    
    templates = await db.import_mapping_templates.find(query, {"_id": 0}).to_list(100)
    return templates

@router.get("/templates/{template_id}", response_model=ImportMappingTemplate)
async def get_import_template(
    template_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get import template by ID"""
    template = await db.import_mapping_templates.find_one({"id": template_id}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return ImportMappingTemplate(**template)

@router.delete("/templates/{template_id}")
async def delete_import_template(
    template_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Delete import template"""
    result = await db.import_mapping_templates.delete_one({"id": template_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template deleted successfully"}
