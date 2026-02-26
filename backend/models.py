from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    SALES = "sales"
    SUPPORT = "support"
    DISPATCH = "dispatch"
    WAREHOUSE = "warehouse"

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DISPATCHED = "dispatched"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"
    REPLACEMENT = "replacement"

class OrderChannel(str, Enum):
    AMAZON = "amazon"
    FLIPKART = "flipkart"
    WHATSAPP = "whatsapp"
    WEBSITE = "website"
    PHONE = "phone"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ClaimType(str, Enum):
    AMAZON_AZ = "amazon_az"
    FLIPKART_DISPUTE = "flipkart_dispute"
    COURIER_DAMAGE = "courier_damage"
    CUSTOMER_RETURN = "customer_return"

class UserBase(BaseModel):
    email: str
    name: str
    role: UserRole
    phone: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User

class CustomerBase(BaseModel):
    name: str
    phone_primary: str
    phone_secondary: Optional[str] = None
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None

class Customer(CustomerBase):
    model_config = ConfigDict(extra="ignore")
    id: str
    created_at: datetime
    total_orders: int = 0

class OrderBase(BaseModel):
    channel: OrderChannel
    order_number: str
    order_date: datetime
    dispatch_by: Optional[datetime] = None
    delivery_by: Optional[datetime] = None
    customer_id: str
    customer_name: str
    phone: str
    phone_secondary: Optional[str] = None
    email: Optional[str] = None
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None
    shipping_address_line1: Optional[str] = None
    shipping_address_line2: Optional[str] = None
    landmark: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: str
    country: Optional[str] = "IN"
    sku: str
    master_sku: Optional[str] = None
    fnsku: Optional[str] = None
    asin: Optional[str] = None
    fsn_id: Optional[str] = None
    product_name: str
    quantity: int = 1
    price: float
    item_tax: Optional[float] = None
    shipping_price: Optional[float] = None
    shipping_tax: Optional[float] = None
    total_amount: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    instructions: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    model_config = ConfigDict(extra="ignore")
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    dispatch_date: Optional[datetime] = None
    delivery_date: Optional[datetime] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    courier_partner: Optional[str] = None
    courier_awb: Optional[str] = None
    pickup_status: Optional[str] = None
    pickup_date: Optional[datetime] = None
    in_transit_date: Optional[datetime] = None
    out_for_delivery_date: Optional[datetime] = None
    delivered_date: Optional[datetime] = None
    rto_initiated_date: Optional[datetime] = None
    rto_delivered_date: Optional[datetime] = None
    return_requested: bool = False
    return_reason: Optional[str] = None
    return_date: Optional[datetime] = None
    return_tracking_number: Optional[str] = None
    return_status: Optional[str] = None
    refund_amount: Optional[float] = None
    refund_date: Optional[datetime] = None
    dc1_called: bool = False  # Day 1 Customer Call (within 24h of order)
    dc1_date: Optional[datetime] = None
    cp_sent: bool = False  # Confirmation Photo Sent (order ready photo)
    assembly_type: Optional[str] = None  # self/paid/free
    paid_assembly: bool = False
    dnp1_conf: bool = False  # Day N-1 Pre-Delivery Confirmation (day before delivery)
    dnp2_conf: bool = False  # Day N-2 Pre-Delivery Confirmation (2 days before)
    dnp3_conf: bool = False  # Day N-3 Pre-Delivery Confirmation (3 days before)
    dp_conf: bool = False  # Day of Delivery Confirmation
    install_conf: bool = False  # Installation Confirmation
    deliver_conf: bool = False  # Delivery Confirmation (customer received)
    review_conf: bool = False  # Review Request Confirmation
    cancellation_reason: Optional[str] = None
    assigned_to: Optional[str] = None
    internal_notes: Optional[str] = None
    fulfillment_channel: Optional[str] = None
    sales_channel: Optional[str] = None
    ship_service_level: Optional[str] = None
    payment_method: Optional[str] = None
    is_business_order: bool = False
    is_prime: bool = False
    last_updated: Optional[datetime] = None

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    dispatch_date: Optional[datetime] = None
    delivery_date: Optional[datetime] = None
    tracking_number: Optional[str] = None
    courier_partner: Optional[str] = None
    dc1_called: Optional[bool] = None
    dc1_date: Optional[datetime] = None
    cp_sent: Optional[bool] = None
    assembly_type: Optional[str] = None
    paid_assembly: Optional[bool] = None
    dnp1_conf: Optional[bool] = None
    dnp2_conf: Optional[bool] = None
    dnp3_conf: Optional[bool] = None
    dp_conf: Optional[bool] = None
    install_conf: Optional[bool] = None
    deliver_conf: Optional[bool] = None
    review_conf: Optional[bool] = None
    pickup_status: Optional[str] = None
    cancellation_reason: Optional[str] = None
    assigned_to: Optional[str] = None
    internal_notes: Optional[str] = None

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: str = "medium"
    assigned_to: Optional[str] = None
    order_id: Optional[str] = None
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    model_config = ConfigDict(extra="ignore")
    id: str
    created_at: datetime
    created_by: str
    completed_at: Optional[datetime] = None

class CommunicationLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    order_id: str
    customer_id: str
    type: str
    message: str
    status: str
    created_at: datetime
    sent_by: Optional[str] = None

class ProductBase(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Optional[Dict[str, float]] = None
    num_boxes: int = 1
    stock_quantity: int = 0
    reorder_level: int = 10
    price: float
    cost: Optional[float] = None

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    model_config = ConfigDict(extra="ignore")
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class CourierPartner(BaseModel):
    model_config = ConfigDict(extra="ignore")


# Master SKU Mapping Models
class MasterSKUMapping(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    master_sku: str
    product_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    amazon_sku: Optional[str] = None
    amazon_asin: Optional[str] = None
    amazon_fnsku: Optional[str] = None
    flipkart_sku: Optional[str] = None
    flipkart_fsn: Optional[str] = None
    website_sku: Optional[str] = None
    dimensions: Optional[str] = None
    weight: Optional[float] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class MasterSKUMappingCreate(BaseModel):
    master_sku: str
    product_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    amazon_sku: Optional[str] = None
    amazon_asin: Optional[str] = None
    amazon_fnsku: Optional[str] = None
    flipkart_sku: Optional[str] = None
    flipkart_fsn: Optional[str] = None
    website_sku: Optional[str] = None
    dimensions: Optional[str] = None
    weight: Optional[float] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None

# Import Mapping Template Models
class ImportMappingTemplate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    channel: str
    description: Optional[str] = None
    column_mappings: Dict[str, str]  # {"csv_column": "system_field"}
    date_format: Optional[str] = None
    delimiter: Optional[str] = ","
    has_header: bool = True
    is_default: bool = False
    created_at: datetime
    created_by: str

class ImportMappingTemplateCreate(BaseModel):
    name: str
    channel: str
    description: Optional[str] = None
    column_mappings: Dict[str, str]
    date_format: Optional[str] = None
    delimiter: Optional[str] = ","
    has_header: bool = True
    is_default: bool = False

# Return Management Models
class ReturnReason(str, Enum):
    DEFECTIVE = "defective"
    DAMAGED = "damaged"
    WRONG_ITEM = "wrong_item"
    NOT_AS_DESCRIBED = "not_as_described"
    SIZE_ISSUE = "size_issue"
    QUALITY_ISSUE = "quality_issue"
    CUSTOMER_CHANGED_MIND = "customer_changed_mind"
    DELIVERY_DELAY = "delivery_delay"
    OTHER = "other"

class ReturnStatus(str, Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    PICKUP_SCHEDULED = "pickup_scheduled"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    INSPECTED = "inspected"
    REFUNDED = "refunded"
    REPLACED = "replaced"

class DamageCategory(str, Enum):
    SCRATCH = "scratch"
    CRACK = "crack"
    DENT = "dent"
    BROKEN = "broken"
    MISSING_PARTS = "missing_parts"
    PACKAGING_DAMAGE = "packaging_damage"
    NO_DAMAGE = "no_damage"

class ReturnRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    order_id: str
    order_number: str
    customer_id: str
    customer_name: str
    phone: str
    return_reason: ReturnReason
    return_reason_details: Optional[str] = None
    damage_category: Optional[DamageCategory] = None
    return_status: ReturnStatus
    requested_date: datetime
    approved_date: Optional[datetime] = None
    pickup_date: Optional[datetime] = None
    received_date: Optional[datetime] = None
    inspection_date: Optional[datetime] = None
    refund_date: Optional[datetime] = None
    return_tracking_number: Optional[str] = None
    courier_partner: Optional[str] = None
    qc_notes: Optional[str] = None
    is_installation_related: bool = False
    batch_number: Optional[str] = None
    damage_images: Optional[List[str]] = []
    refund_amount: Optional[float] = None
    refund_method: Optional[str] = None
    replacement_order_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class ReturnRequestCreate(BaseModel):
    order_id: str
    return_reason: ReturnReason
    return_reason_details: Optional[str] = None
    damage_category: Optional[DamageCategory] = None
    is_installation_related: bool = False
    damage_images: Optional[List[str]] = []

# Channel Management Models
class Channel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    display_name: str
    is_active: bool = True
    required_fields: List[str] = []
    optional_fields: List[str] = []
    supports_tracking: bool = True
    commission_rate: Optional[float] = None
    created_at: datetime

class ChannelCreate(BaseModel):
    name: str
    display_name: str
    is_active: bool = True
    required_fields: List[str] = []
    optional_fields: List[str] = []
    supports_tracking: bool = True
    commission_rate: Optional[float] = None

    id: str
    name: str
    base_rate: float
    per_kg_rate: float
    performance_score: float = 0.0
    active: bool = True
    service_pincodes: Optional[List[str]] = None

class ClaimBase(BaseModel):
    order_id: str
    type: ClaimType
    amount: float
    description: str
    status: str = "filed"

class ClaimCreate(ClaimBase):
    pass

class Claim(ClaimBase):
    model_config = ConfigDict(extra="ignore")
    id: str
    created_at: datetime
    filed_by: str
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None

class DashboardStats(BaseModel):
    total_orders: int
    pending_orders: int
    dispatched_today: int
    pending_tasks: int
    pending_calls: int
    low_stock_items: int
    pending_claims: int
    revenue_today: float
