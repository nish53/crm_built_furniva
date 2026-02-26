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
    dc1_called: bool = False
    dc1_date: Optional[datetime] = None
    cp_sent: bool = False
    assembly_type: Optional[str] = None
    paid_assembly: bool = False
    dnp1_conf: bool = False
    dnp2_conf: bool = False
    dnp3_conf: bool = False
    dp_conf: bool = False
    install_conf: bool = False
    deliver_conf: bool = False
    review_conf: bool = False
    cancellation_reason: Optional[str] = None
    assigned_to: Optional[str] = None
    internal_notes: Optional[str] = None
    fulfillment_channel: Optional[str] = None
    sales_channel: Optional[str] = None
    ship_service_level: Optional[str] = None
    payment_method: Optional[str] = None
    is_business_order: bool = False
    is_prime: bool = False
    gift_message: Optional[str] = None
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
