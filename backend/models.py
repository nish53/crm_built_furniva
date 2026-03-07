from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, TypeVar, Generic
from datetime import datetime
from enum import Enum

# Generic type for paginated responses
T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

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
    HISTORICAL = "historical"

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
    sku: Optional[str] = None
    master_sku: Optional[str] = None
    fnsku: Optional[str] = None
    asin: Optional[str] = None
    fsn_id: Optional[str] = None
    product_name: Optional[str] = None
    quantity: int = 1
    price: float
    item_tax: Optional[float] = None
    shipping_price: Optional[float] = None
    shipping_tax: Optional[float] = None
    total_amount: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    master_status: Optional[List[str]] = []  # Multi-status: ["pending_dispatch", "in_transit", "delivered", "installation_pending", "return_requested", "replacement_pending"]
    instructions: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    cancellation_reason: Optional[str] = None

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
    
    # Historical communication tracking
    order_conf_calling: bool = False  # Order Confirmation Call
    dispatch_conf_sent: bool = False  # Dispatch Confirmation Sent
    dnp_day1: bool = False  # Did Not Pick Day 1
    confirmed_day1: bool = False  # Confirmed on Day 1
    dnp_day2: bool = False  # Did Not Pick Day 2
    confirmed_day2: bool = False  # Confirmed on Day 2
    dnp_day3: bool = False  # Did Not Pick Day 3
    confirmed_day3: bool = False  # Confirmed on Day 3
    
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
    
    # Loss Calculation Fields
    logistics_cost_outbound: Optional[float] = 0.0  # Cost to ship to customer
    logistics_cost_return: Optional[float] = 0.0  # Cost for return shipping
    product_cost: Optional[float] = 0.0  # Actual product cost (from master SKU or manual)
    replacement_parts_cost: Optional[float] = 0.0  # Cost of replacement parts
    total_loss: Optional[float] = 0.0  # Calculated total loss
    loss_category: Optional[str] = None  # pfc, resolved, refunded, fraud
    loss_calculation_method: Optional[str] = "auto"  # auto or manual
    loss_edited_by: Optional[str] = None  # User who edited loss
    loss_edited_at: Optional[datetime] = None  # When loss was edited
    loss_notes: Optional[str] = None  # Notes about loss calculation
    
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
    photos: Optional[List[str]] = []  # URLs to task photos
    order_details: Optional[str] = None  # Order number or details for reference

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
    listings_created: Optional[List[str]] = []  # Auto-created listings
    orders_updated: Optional[int] = 0  # Count of orders updated

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
    column_mappings: Dict[str, str]
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


# Platform Listings (One Master SKU can have MULTIPLE listings per platform)
class PlatformListing(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    master_sku: str
    platform: str  # amazon, flipkart, website, etc.
    platform_sku: Optional[str] = None  # Seller SKU
    platform_product_id: Optional[str] = None  # ASIN for Amazon, FSN for Flipkart
    platform_fnsku: Optional[str] = None  # FNSKU
    listing_title: Optional[str] = None
    listing_url: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

class PlatformListingCreate(BaseModel):
    master_sku: str
    platform: str
    platform_sku: Optional[str] = None
    platform_product_id: Optional[str] = None
    platform_fnsku: Optional[str] = None
    listing_title: Optional[str] = None
    listing_url: Optional[str] = None
    is_active: bool = True

# Procurement Batches (Cost tracking per batch)
class BoxDimension(BaseModel):
    length: float = 0
    width: float = 0
    height: float = 0

class ProcurementBatch(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    master_sku: str
    batch_number: str
    procurement_date: datetime
    quantity: int
    unit_cost: float
    total_cost: float
    num_boxes: int = 1
    box_weights: List[float] = []
    total_weight: float = 0.0
    box_dimensions: List[Dict[str, float]] = []
    supplier: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

class ProcurementBatchCreate(BaseModel):
    master_sku: str
    batch_number: str
    procurement_date: datetime
    quantity: int
    unit_cost: float
    num_boxes: int = 1
    box_weights: List[float] = []
    box_dimensions: List[Dict[str, float]] = []
    supplier: Optional[str] = None
    notes: Optional[str] = None

# Return Management Models
class ReturnReason(str, Enum):
    # Historical reasons from user's data
    PFC = "PFC"
    DELAY = "Delay"
    DAMAGE = "Damage"
    DAMAGED_AND_PENDING = "damaged and pending"
    DAMAGED_AND_REPLACED = "damaged and replaced"
    HARDWARE_MISSING = "Hardware Missing"
    CUSTOMER_ISSUE = "Customer Issue"
    FRAUD = "Fraud"
    CANCELLED_AND_DELIVERED = "cancelled and delivered"
    STATUS_PENDING = "Status Pending"
    
    # Standard return reasons
    DEFECTIVE_PRODUCT = "Defective Product"
    DAMAGED_IN_TRANSIT = "Damaged in Transit"
    WRONG_ITEM_DELIVERED = "Wrong Item Delivered"
    NOT_AS_DESCRIBED = "Not as Described"
    SIZE_ISSUE = "Size Issue"
    QUALITY_ISSUE = "Quality Issue"
    CUSTOMER_CHANGED_MIND = "Customer Changed Mind"
    DELIVERY_DELAY = "Delivery Delay"
    OTHER = "Other"

class ReturnType(str, Enum):
    RETURN = "return"
    REPLACEMENT = "replacement"

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
    NO_DAMAGE = "No Damage"
    SCRATCH = "Scratch"
    CRACK = "Crack"
    DENT = "Dent"
    BROKEN = "Broken"
    MISSING_PARTS = "Missing Parts"
    PACKAGING_DAMAGE = "Packaging Damage"
    HARDWARE_MISSING = "Hardware Missing"
    PARTS_MISSING = "Parts Missing"

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
    previous_status: Optional[str] = None
    status_history: List[Dict[str, Any]] = []
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
    created_at: datetime
    updated_at: Optional[datetime] = None

class ReturnRequestCreate(BaseModel):
    order_id: str
    return_reason: ReturnReason
    return_reason_details: Optional[str] = None
    damage_category: Optional[DamageCategory] = None
    is_installation_related: bool = False
    damage_images: Optional[List[str]] = []



# Replacement Request Models (Separate from Return)
class ReplacementReason(str, Enum):
    DAMAGE = "Damage"
    QUALITY_ISSUE = "Quality Issue"

class ReplacementStatus(str, Enum):
    PENDING = "Replacement Pending"
    PRIORITY_REVIEW = "Priority Review"
    SHIP_REPLACEMENT = "Ship Replacement"
    TRACKING_ADDED = "Tracking Added"
    DELIVERED = "Delivered"
    RESOLVED = "Issue Resolved"
    NOT_RESOLVED = "Issue Not Resolved"

class ReplacementRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    order_id: str
    order_number: str
    customer_id: str
    customer_name: str
    phone: str
    replacement_reason: ReplacementReason  # Only Damage or Quality Issue
    damage_description: str  # Detailed description of what's damaged
    replacement_status: ReplacementStatus
    damage_images: List[str] = []  # Image URLs (mandatory)
    requested_date: datetime
    priority_review_date: Optional[datetime] = None
    ship_date: Optional[datetime] = None
    tracking_number: Optional[str] = None
    tracking_added_date: Optional[datetime] = None
    delivered_date: Optional[datetime] = None
    resolved_date: Optional[datetime] = None
    issue_resolved: Optional[bool] = None  # Yes/No after delivery
    resolution_notes: Optional[str] = None
    courier_partner: Optional[str] = None
    replacement_cost: Optional[float] = None
    status_history: List[Dict[str, Any]] = []
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class ReplacementRequestCreate(BaseModel):
    order_id: str
    replacement_reason: ReplacementReason
    damage_description: str  # Required detailed description
    damage_images: List[str]  # Mandatory image URLs

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


# Loss Calculation Configuration
class LossConfiguration(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "loss_config"  # Single document
    
    # Configurable percentages and variables
    pfc_loss_percentage: float = 0.0  # PFC has 0% loss
    resolved_cost_percentage: float = 15.0  # Resolved costs 15% of price (user configurable)
    
    # Default logistics costs (can be overridden per order)
    default_outbound_logistics: float = 100.0  # Default shipping cost
    default_return_logistics: float = 100.0  # Default return cost
    
    # Calculation rules
    refunded_includes_product_cost_if_damage: bool = True  # Add product cost if damage-related
    fraud_includes_product_and_logistics: bool = True  # Fraud = product + both logistics
    
    updated_at: datetime
    updated_by: str

class LossConfigurationUpdate(BaseModel):
    pfc_loss_percentage: Optional[float] = None
    resolved_cost_percentage: Optional[float] = None
    default_outbound_logistics: Optional[float] = None
    default_return_logistics: Optional[float] = None
    refunded_includes_product_cost_if_damage: Optional[bool] = None
    fraud_includes_product_and_logistics: Optional[bool] = None

class OrderLossUpdate(BaseModel):
    logistics_cost_outbound: Optional[float] = None
    logistics_cost_return: Optional[float] = None
    product_cost: Optional[float] = None
    replacement_parts_cost: Optional[float] = None
    total_loss: Optional[float] = None
    loss_notes: Optional[str] = None

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
