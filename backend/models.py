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
    AMZ = "amz"  # Amazon short form
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

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    model_config = ConfigDict(extra="ignore")
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    previous_status: Optional[str] = None  # For undo functionality
    status_changed_at: Optional[datetime] = None
    status_changed_by: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[str] = None
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
    REQUESTED = "requested"  # 1. Customer initiates return
    FEEDBACK_CHECK = "feedback_check"  # 2. Check for negative reviews
    CLAIM_FILED = "claim_filed"  # 3. Customer filed marketplace claim
    AUTHORIZED = "authorized"  # 4. Return authorized (auto or manual)
    RETURN_INITIATED = "return_initiated"  # 5. Customer shipped back
    IN_TRANSIT = "in_transit"  # 6. Return shipment tracking
    WAREHOUSE_RECEIVED = "warehouse_received"  # 7. Back in warehouse
    QC_INSPECTION = "qc_inspection"  # 8. Quality check
    CLAIM_FILING = "claim_filing"  # 9. Filing courier/insurance claim
    CLAIM_STATUS = "claim_status"  # 10. Claim approved/rejected/pending
    REFUND_PROCESSED = "refund_processed"  # 11. Refund issued
    CLOSED = "closed"  # 12. Return complete
    REJECTED = "rejected"  # Return rejected
    CANCELLED = "cancelled"  # Return cancelled

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
    previous_status: Optional[str] = None
    status_history: List[Dict[str, Any]] = []
    
    # Stage-specific fields
    requested_date: datetime
    
    # Feedback check
    has_negative_feedback: Optional[bool] = None
    feedback_platform: Optional[str] = None  # amazon, flipkart, google
    feedback_details: Optional[str] = None
    
    # Customer claim filed
    customer_claim_filed: Optional[bool] = None
    customer_claim_type: Optional[str] = None  # a_to_z, safe_t, other
    customer_claim_id: Optional[str] = None
    
    # Authorization
    authorized_date: Optional[datetime] = None
    authorized_by: Optional[str] = None
    authorization_type: Optional[str] = None  # auto, manual
    
    # Return shipping
    return_initiated_date: Optional[datetime] = None
    return_tracking_number: Optional[str] = None
    courier_partner: Optional[str] = None
    
    # Warehouse
    warehouse_received_date: Optional[datetime] = None
    received_by: Optional[str] = None
    
    # QC Inspection
    inspection_date: Optional[datetime] = None
    qc_passed: Optional[bool] = None
    qc_notes: Optional[str] = None
    damage_severity: Optional[str] = None  # minor, moderate, severe
    damage_images: Optional[List[str]] = []
    product_condition: Optional[str] = None  # sellable, refurbish_needed, scrap
    
    # Courier/Insurance claim
    claim_filed_date: Optional[datetime] = None
    claim_type: Optional[str] = None  # courier_damage, insurance
    claim_amount: Optional[float] = None
    claim_against: Optional[str] = None  # courier name
    claim_reference: Optional[str] = None
    claim_status: Optional[str] = None  # pending, approved, rejected, partial
    claim_approved_amount: Optional[float] = None
    claim_documents: Optional[List[str]] = []
    
    # Refund
    refund_date: Optional[datetime] = None
    refund_amount: Optional[float] = None
    refund_method: Optional[str] = None
    refund_reference: Optional[str] = None
    
    # Closure
    closed_date: Optional[datetime] = None
    resolution: Optional[str] = None  # refunded, replaced, repaired, customer_kept
    
    is_installation_related: bool = False
    batch_number: Optional[str] = None
    replacement_order_id: Optional[str] = None
    internal_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class ReturnRequestCreate(BaseModel):
    order_id: str
    return_reason: ReturnReason
    return_reason_details: Optional[str] = None
    damage_category: Optional[DamageCategory] = None
    is_installation_related: bool = False
    damage_images: Optional[List[str]] = []



class ReplacementStatus(str, Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    PARTS_ARRANGED = "parts_arranged"
    DISPATCHED = "dispatched"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    INSTALLED = "installed"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"

class ReplacementRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    order_id: str
    order_number: str
    return_id: Optional[str] = None  # Link to parent return request
    customer_id: str
    customer_name: str
    phone: str
    
    # Replacement details
    replacement_type: str  # full_product, parts, repair
    damage_description: str
    damage_images: Optional[List[str]] = []
    parts_needed: Optional[List[str]] = []  # List of part names/SKUs
    
    # Status tracking
    replacement_status: ReplacementStatus
    previous_status: Optional[str] = None
    status_history: List[Dict[str, Any]] = []
    
    # Workflow stages
    requested_date: datetime
    approved_date: Optional[datetime] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    parts_arranged_date: Optional[datetime] = None
    parts_cost: Optional[float] = None
    
    dispatch_date: Optional[datetime] = None
    tracking_number: Optional[str] = None
    courier_partner: Optional[str] = None
    
    delivery_date: Optional[datetime] = None
    installation_date: Optional[datetime] = None
    installer_name: Optional[str] = None
    installation_notes: Optional[str] = None
    
    resolved_date: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    customer_satisfied: Optional[bool] = None
    
    # Costs
    replacement_cost: Optional[float] = None
    logistics_cost: Optional[float] = None
    installation_cost: Optional[float] = None
    total_cost: Optional[float] = None
    
    internal_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class ReplacementRequestCreate(BaseModel):
    order_id: str
    return_id: Optional[str] = None
    replacement_type: str
    damage_description: str
    parts_needed: Optional[List[str]] = []

class ClaimStatus(str, Enum):
    DRAFT = "draft"
    FILED = "filed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PARTIALLY_APPROVED = "partially_approved"
    REJECTED = "rejected"
    APPEALED = "appealed"
    CLOSED = "closed"

class ClaimType(str, Enum):
    COURIER_DAMAGE = "courier_damage"
    MARKETPLACE_AZ = "marketplace_a_to_z"
    MARKETPLACE_SAFET = "marketplace_safe_t"
    INSURANCE = "insurance"
    WARRANTY = "warranty"
    OTHER = "other"

class Claim(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    
    # Related entities
    order_id: Optional[str] = None
    order_number: Optional[str] = None
    return_id: Optional[str] = None
    replacement_id: Optional[str] = None
    
    # Claim details
    claim_type: ClaimType
    claim_against: str  # Courier name, marketplace, insurance company
    claim_amount: float
    claim_description: str
    claim_reference: Optional[str] = None  # External claim ID/ticket number
    
    # Status
    claim_status: ClaimStatus
    previous_status: Optional[str] = None
    status_history: List[Dict[str, Any]] = []
    
    # Dates
    filed_date: datetime
    expected_resolution_date: Optional[datetime] = None
    resolution_date: Optional[datetime] = None
    
    # Resolution
    approved_amount: Optional[float] = None
    rejection_reason: Optional[str] = None
    appeal_notes: Optional[str] = None
    
    # Documents
    supporting_documents: Optional[List[str]] = []
    evidence_images: Optional[List[str]] = []
    correspondence: Optional[List[Dict[str, Any]]] = []
    
    # Assignment
    assigned_to: Optional[str] = None
    filed_by: str
    
    internal_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class ClaimCreate(BaseModel):
    order_id: Optional[str] = None
    return_id: Optional[str] = None
    replacement_id: Optional[str] = None
    claim_type: ClaimType
    claim_against: str
    claim_amount: float
    claim_description: str
    claim_reference: Optional[str] = None
    expected_resolution_date: Optional[datetime] = None

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
