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
    COURIER_DAMAGE = "courier_damage"
    MARKETPLACE_A_TO_Z = "marketplace_a_to_z"
    MARKETPLACE_SAFE_T = "marketplace_safe_t"
    INSURANCE = "insurance"
    WARRANTY = "warranty"
    OTHER = "other"
    # Legacy types for backward compatibility
    AMAZON_AZ = "amazon_az"
    FLIPKART_DISPUTE = "flipkart_dispute"
    CUSTOMER_RETURN = "customer_return"

class ClaimStatus(str, Enum):
    DRAFT = "draft"
    FILED = "filed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PARTIALLY_APPROVED = "partially_approved"
    REJECTED = "rejected"
    APPEALED = "appealed"
    CLOSED = "closed"

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
    
    # Status tracking
    previous_status: Optional[str] = None  # For undo functionality
    cancelled_at: Optional[datetime] = None  # When order was cancelled
    cancelled_by: Optional[str] = None  # Who cancelled the order
    
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
# Context-dependent cancellation/return reason enums
class PostDeliveryReturnReason(str, Enum):
    """Reasons for returns after order is delivered"""
    DAMAGE = "damage"
    CUSTOMER_ISSUES_EXCEPT_QUALITY = "customer_issues_except_quality"
    HARDWARE_MISSING = "hardware_missing"
    DEFECTIVE_PRODUCT = "defective_product"
    FRAUD_CUSTOMER = "fraud_customer"
    WRONG_PRODUCT_SENT = "wrong_product_sent"
    CUSTOMER_QUALITY_ISSUES = "customer_quality_issues"
    PRODUCT_DELAYED_CUSTOMER_ACCEPTED = "product_delayed_customer_accepted"

class InTransitCancelReason(str, Enum):
    """Reasons for cancellation when order is in transit (RTO)"""
    CUSTOMER_REFUSED_DOORSTEP = "customer_refused_doorstep"
    CUSTOMER_UNAVAILABLE = "customer_unavailable"
    DELAY = "delay"

class PreDispatchCancelReason(str, Enum):
    """Reasons for cancellation before order is dispatched"""
    CHANGE_OF_MIND = "change_of_mind"
    FOUND_BETTER_PRICING = "found_better_pricing"
    ORDERED_MISTAKENLY = "ordered_mistakenly"
    WANTS_TO_CUSTOMIZE = "wants_to_customize"
    DID_NOT_SPECIFY = "did_not_specify"
    CUSTOMER_NOT_AVAILABLE = "customer_not_available"

# Legacy enum for backward compatibility
class ReturnReason(str, Enum):
    """DEPRECATED - Use context-dependent enums above"""
    DAMAGE = "Damage"
    CUSTOMER_REFUSED = "Customer Refused at Doorstep"
    FRAUD = "Fraud"
    DELAYED = "Delayed"
    WRONG_ITEM = "Wrong Item Delivered"
    QUALITY_ISSUE = "Customer Quality Issue"
    MISSING_ITEM = "Missing Item"
    PRE_FULFILLMENT_CANCEL = "Pre Fulfillment Cancel"

class ReturnType(str, Enum):
    RETURN = "return"
    REPLACEMENT = "replacement"

class ReturnStatus(str, Enum):
    """Status for 3-type return workflow"""
    # Core statuses
    REQUESTED = "requested"
    APPROVED = "approved"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CLOSED = "closed"
    # In-transit RTO specific
    RTO_IN_TRANSIT = "rto_in_transit"
    # Post-delivery pickup specific
    PICKED_UP = "picked_up"  # Changed from pickup_scheduled
    PICKUP_IN_TRANSIT = "pickup_in_transit"
    PICKUP_NOT_REQUIRED = "pickup_not_required"
    # Warehouse phase
    WAREHOUSE_RECEIVED = "warehouse_received"
    CONDITION_CHECKED = "condition_checked"
    # Legacy statuses (backward compatibility)
    FEEDBACK_CHECK = "feedback_check"
    CLAIM_FILED = "claim_filed"
    AUTHORIZED = "authorized"
    RETURN_INITIATED = "return_initiated"
    IN_TRANSIT = "in_transit"
    QC_INSPECTION = "qc_inspection"
    CLAIM_FILING = "claim_filing"
    CLAIM_STATUS = "claim_status"
    REFUND_PROCESSED = "refund_processed"
    CANCELLED = "cancelled"
    RECEIVED = "received"
    INSPECTED = "inspected"
    REFUNDED = "refunded"
    REPLACED = "replaced"

class DamageCategory(str, Enum):
    DENT = "Dent"
    BROKEN = "Broken"
    SCRATCHES = "Scratches"
    CRACK = "Crack"

class ReturnRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    order_id: str
    order_number: str
    customer_id: str
    customer_name: str
    phone: str
    return_reason: Optional[str] = None  # Changed to Optional[str] for flexibility with old and new data
    return_reason_details: Optional[str] = None
    damage_category: Optional[DamageCategory] = None
    return_status: ReturnStatus
    previous_status: Optional[str] = None
    status_history: List[Dict[str, Any]] = []
    category: Optional[str] = None  # pfc, resolved, refunded, fraud
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
    
    # Feedback check stage fields
    feedback_check_date: Optional[datetime] = None
    feedback_check_notes: Optional[str] = None
    feedback_check_outcome: Optional[str] = None  # proceed, resolved_at_feedback
    customer_feedback: Optional[str] = None
    
    # Claim filed stage fields
    claim_filed_date: Optional[datetime] = None
    claim_reference: Optional[str] = None
    claim_platform: Optional[str] = None  # amazon, flipkart, courier
    claim_amount: Optional[float] = None
    
    # Authorization stage fields
    authorized_date: Optional[datetime] = None
    authorized_by: Optional[str] = None
    authorization_notes: Optional[str] = None
    
    # Return initiated stage fields
    return_initiated_date: Optional[datetime] = None
    return_method: Optional[str] = None  # courier_pickup, customer_drop, reverse_logistics
    
    # Warehouse received stage fields
    warehouse_received_date: Optional[datetime] = None
    warehouse_received_by: Optional[str] = None
    warehouse_notes: Optional[str] = None
    
    # QC inspection stage fields
    qc_inspection_date: Optional[datetime] = None
    qc_inspector: Optional[str] = None
    qc_result: Optional[str] = None  # pass, fail, partial
    qc_images: Optional[List[str]] = []
    qc_damage_found: Optional[str] = None
    
    # Claim filing stage fields (post-QC claim to marketplace/courier)
    claim_filing_date: Optional[datetime] = None
    claim_filing_reference: Optional[str] = None
    claim_filing_platform: Optional[str] = None
    claim_filing_amount: Optional[float] = None
    claim_filing_notes: Optional[str] = None
    
    # Claim status stage fields
    claim_status_date: Optional[datetime] = None
    claim_status_result: Optional[str] = None  # approved, rejected, partial
    claim_approved_amount: Optional[float] = None
    claim_status_notes: Optional[str] = None
    
    # Refund processed stage fields
    refund_processed_date: Optional[datetime] = None
    refund_processed_amount: Optional[float] = None
    refund_processed_method: Optional[str] = None
    refund_transaction_id: Optional[str] = None
    
    # Closure fields
    closed_date: Optional[datetime] = None
    closed_by: Optional[str] = None
    closure_notes: Optional[str] = None
    resolution_summary: Optional[str] = None
    
    # NEW FIELDS FOR 3-TYPE WORKFLOW
    return_type: Optional[str] = None  # "pre_dispatch" | "in_transit" | "post_delivery"
    cancellation_reason: Optional[str] = None  # Actual reason value from appropriate enum
    notes: Optional[str] = None  # Additional notes from user
    
    # Pickup phase fields (post-delivery only)
    pickup_not_required: bool = False  # Skip pickup for severely damaged items
    pickup_tracking_id: Optional[str] = None
    pickup_courier: Optional[str] = None
    
    # Condition check fields (post-delivery only)
    received_condition: Optional[str] = None  # "mint" | "damaged"
    condition_notes: Optional[str] = None
    
    # RTO phase fields (in-transit only)
    rto_tracking_number: Optional[str] = None
    rto_courier: Optional[str] = None
    
    created_at: datetime
    updated_at: Optional[datetime] = None

class ReturnRequestCreate(BaseModel):
    order_id: str
    return_reason: str  # Changed from ReturnReason enum to str to accept context-dependent reasons
    return_reason_details: Optional[str] = None
    damage_category: Optional[DamageCategory] = None
    is_installation_related: bool = False
    damage_images: Optional[List[str]] = []



# Replacement Request Models (Separate from Return)
class ReplacementReason(str, Enum):
    """Reasons for filing a replacement request"""
    DAMAGED = "damaged"
    QUALITY = "quality"
    WRONG_PRODUCT_SENT = "wrong_product_sent"
    CUSTOMER_CHANGE_OF_MIND = "customer_change_of_mind"

class ReplacementType(str, Enum):
    """Type of replacement requested"""
    FULL = "full_replacement"
    PARTIAL = "partial_replacement"

class ReplacementStatus(str, Enum):
    """Status for replacement workflow"""
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    PICKED_UP = "picked_up"  # Changed from pickup_scheduled
    PICKUP_IN_TRANSIT = "pickup_in_transit"
    PICKUP_NOT_REQUIRED = "pickup_not_required"
    WAREHOUSE_RECEIVED = "warehouse_received"
    NEW_SHIPMENT_DISPATCHED = "new_shipment_dispatched"
    PARTS_SHIPPED = "parts_shipped"  # For partial replacement
    DELIVERED = "delivered"
    RESOLVED = "resolved"
    # Legacy statuses for backward compatibility
    PENDING = "Replacement Pending"
    PRIORITY_REVIEW = "Priority Review"
    SHIP_REPLACEMENT = "Ship Replacement"
    TRACKING_ADDED = "Tracking Added"
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
    
    # NEW FIELDS FOR FULL/PARTIAL REPLACEMENT WORKFLOW
    replacement_type: Optional[str] = None  # "full_replacement" | "partial_replacement"
    difference_amount: Optional[float] = None  # For customer change of mind (upsell)
    notes: Optional[str] = None  # Additional notes
    
    # Pickup phase fields
    pickup_not_required: bool = False  # Skip pickup for severe damage
    pickup_date: Optional[datetime] = None
    pickup_tracking_id: Optional[str] = None
    pickup_courier: Optional[str] = None
    warehouse_received_date: Optional[datetime] = None
    received_condition: Optional[str] = None  # "mint" | "damaged"
    condition_notes: Optional[str] = None
    
    # New shipment phase fields
    new_tracking_id: Optional[str] = None
    new_courier: Optional[str] = None
    items_sent_description: Optional[str] = None  # What's being sent
    
    # Partial replacement specific fields
    parts_description: Optional[str] = None  # What parts are being sent
    parts_tracking_id: Optional[str] = None
    parts_courier: Optional[str] = None
    
    # Delivery confirmation
    delivery_confirmed: bool = False
    
    # DUAL APPROVAL FIELDS (Bug #6)
    pickup_approved: bool = False  # Approval to collect old product
    pickup_approved_date: Optional[datetime] = None
    pickup_approved_by: Optional[str] = None
    replacement_approved: bool = False  # Approval to send new product
    replacement_approved_date: Optional[datetime] = None
    replacement_approved_by: Optional[str] = None
    
    # Previous status for undo functionality (Bug #3)
    previous_status: Optional[str] = None

class ReplacementRequestCreate(BaseModel):
    order_id: str
    replacement_reason: ReplacementReason
    replacement_type: str  # "full_replacement" | "partial_replacement"
    damage_description: Optional[str] = None  # Optional - only required for damaged reason
    damage_images: Optional[List[str]] = []  # Optional - only required for damaged reason
    notes: Optional[str] = None  # Additional notes
    difference_amount: Optional[float] = None  # For customer change of mind

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
    status: ClaimStatus = ClaimStatus.FILED
    platform: Optional[str] = None  # amazon, flipkart, courier company name
    reference_number: Optional[str] = None  # Platform claim reference

class ClaimCreate(ClaimBase):
    pass

class Claim(ClaimBase):
    model_config = ConfigDict(extra="ignore")
    id: str
    created_at: datetime
    filed_by: str
    updated_at: Optional[datetime] = None
    
    # Status tracking
    status_history: List[Dict[str, Any]] = []
    
    # Approval/rejection
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    approved_amount: Optional[float] = None
    rejection_reason: Optional[str] = None
    
    # Documents and evidence
    documents: List[Dict[str, Any]] = []  # {url, filename, uploaded_at, type}
    evidence_images: List[str] = []
    
    # Correspondence log
    correspondence: List[Dict[str, Any]] = []  # {date, from, to, message, type}
    
    # Resolution
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    resolution_amount: Optional[float] = None


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



# Edit History Tracking
class FieldChange(BaseModel):
    field_name: str
    old_value: Any
    new_value: Any
    field_type: Optional[str] = None  # For better display

class EditHistoryEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    order_id: str
    order_number: str
    changes: List[FieldChange]
    edited_by: str  # User email
    edited_at: datetime
    edit_reason: Optional[str] = None  # Optional reason for edit
    ip_address: Optional[str] = None

class EditHistoryCreate(BaseModel):
    order_id: str
    changes: List[FieldChange]
    edit_reason: Optional[str] = None

class DashboardStats(BaseModel):
    total_orders: int
    pending_orders: int
    dispatched_today: int
    pending_tasks: int
    pending_calls: int  # Now represents "Pending Confirmation"
    low_stock_items: int
    pending_claims: int
    revenue_today: float
    open_returns: int = 0
    open_replacements: int = 0
