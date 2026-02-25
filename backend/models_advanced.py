from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Financial Models
class OrderFinancials(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    order_id: str
    order_number: str
    
    # Revenue
    selling_price: float
    marketplace_commission: float = 0.0
    tcs_tds: float = 0.0
    payment_gateway_fee: float = 0.0
    net_revenue: float = 0.0
    
    # Costs
    product_cost: float = 0.0
    shipping_cost: float = 0.0
    packaging_cost: float = 0.0
    installation_cost: float = 0.0
    rto_cost: float = 0.0
    claim_loss: float = 0.0
    total_cost: float = 0.0
    
    # Profit
    gross_profit: float = 0.0
    profit_margin: float = 0.0
    contribution_margin: float = 0.0
    
    # Settlement
    expected_settlement: float = 0.0
    actual_settlement: Optional[float] = None
    settlement_date: Optional[datetime] = None
    settlement_variance: float = 0.0
    
    # Recovery
    claim_filed_amount: float = 0.0
    claim_recovered_amount: float = 0.0
    refund_given: float = 0.0
    refund_recovered: float = 0.0
    
    created_at: datetime
    updated_at: Optional[datetime] = None

# Return Diagnosis Models
class DamageType(str, Enum):
    SCRATCH = "scratch"
    CRACK = "crack"
    DENT = "dent"
    MISSING_HARDWARE = "missing_hardware"
    BROKEN_PART = "broken_part"
    COLOR_MISMATCH = "color_mismatch"
    SIZE_ISSUE = "size_issue"
    POOR_FINISH = "poor_finish"

class ReturnReason(str, Enum):
    DAMAGED_IN_TRANSIT = "damaged_in_transit"
    MANUFACTURING_DEFECT = "manufacturing_defect"
    INSTALLATION_ISSUE = "installation_issue"
    CUSTOMER_CHANGED_MIND = "customer_changed_mind"
    WRONG_PRODUCT = "wrong_product"
    SIZE_NOT_AS_EXPECTED = "size_not_as_expected"
    QUALITY_BELOW_EXPECTATIONS = "quality_below_expectations"
    MISSING_PARTS = "missing_parts"

class ReturnDiagnosis(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    order_id: str
    order_number: str
    sku: str
    product_name: str
    
    # Reason Analysis
    primary_reason: ReturnReason
    secondary_reasons: List[ReturnReason] = []
    is_installation_related: bool = False
    is_product_related: bool = True
    
    # Damage Details
    damage_types: List[DamageType] = []
    damage_severity: str = "minor"  # minor, moderate, severe
    damage_images: List[str] = []
    
    # Location & Pattern
    customer_pincode: str
    customer_state: str
    courier_partner: Optional[str] = None
    
    # Responsibility
    responsible_party: str = "unknown"  # manufacturer, courier, installer, customer
    qc_failed: bool = False
    batch_number: Optional[str] = None
    
    # Customer History
    is_repeat_customer_return: bool = False
    customer_return_count: int = 0
    
    # Notes
    diagnosis_notes: str = ""
    resolution: Optional[str] = None
    
    created_at: datetime
    diagnosed_by: Optional[str] = None

# Installation Models  
class InstallerRating(BaseModel):
    quality: float = 0.0
    timeliness: float = 0.0
    professionalism: float = 0.0
    overall: float = 0.0

class Installation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    order_id: str
    order_number: str
    
    # Assignment
    installer_id: Optional[str] = None
    installer_name: Optional[str] = None
    installer_phone: Optional[str] = None
    assigned_date: Optional[datetime] = None
    
    # Type & Cost
    installation_type: str = "diy"  # diy, paid_customer, paid_company
    quoted_cost: float = 0.0
    actual_cost: float = 0.0
    advance_paid: float = 0.0
    balance_paid: float = 0.0
    
    # Scheduling
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    is_delayed: bool = False
    delay_hours: int = 0
    delay_reason: Optional[str] = None
    
    # Communication
    assembly_video_sent: bool = False
    assembly_instructions_sent: bool = False
    customer_confirmed: bool = False
    
    # Verification
    completion_proof_images: List[str] = []
    customer_signature: Optional[str] = None
    
    # Rating
    rating: Optional[InstallerRating] = None
    customer_feedback: Optional[str] = None
    
    # Status
    status: str = "pending"  # pending, assigned, in_progress, completed, cancelled
    
    created_at: datetime
    updated_at: Optional[datetime] = None

# QC Tracking Models
class QCChecklist(BaseModel):
    product_match: bool = False
    dimensions_verified: bool = False
    finish_quality: bool = False
    hardware_complete: bool = False
    packaging_intact: bool = False
    polishing_done: bool = False
    bubble_wrap_done: bool = False
    corners_protected: bool = False
    labeling_correct: bool = False
    weight_verified: bool = False

class QualityControl(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    order_id: str
    order_number: str
    sku: str
    batch_number: Optional[str] = None
    
    # QC Details
    checklist: QCChecklist
    overall_pass: bool = False
    qc_score: float = 0.0
    
    # Images
    before_packaging_images: List[str] = []
    after_packaging_images: List[str] = []
    
    # Personnel
    qc_done_by: Optional[str] = None
    qc_date: datetime
    
    # Issues
    issues_found: List[str] = []
    corrective_actions: List[str] = []
    
    # Manufacturing
    manufacturer_id: Optional[str] = None
    production_date: Optional[datetime] = None
    
    created_at: datetime

# Escalation Models
class EscalationType(str, Enum):
    HIGH_VALUE_ORDER = "high_value_order"
    NEGATIVE_SENTIMENT = "negative_sentiment"
    REPEATED_DNP = "repeated_dnp"
    LATE_DELIVERY = "late_delivery"
    REFUND_REQUEST = "refund_request"
    CLAIM_DISPUTE = "claim_dispute"
    QUALITY_ISSUE = "quality_issue"
    CUSTOMER_ABUSE = "customer_abuse"

class Escalation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    order_id: str
    order_number: str
    
    # Escalation Details
    type: EscalationType
    severity: str = "medium"  # low, medium, high, critical
    triggered_by: str = "system"  # system, user
    trigger_reason: str
    
    # Assignment
    escalated_to: Optional[str] = None
    escalated_at: datetime
    
    # Resolution
    status: str = "open"  # open, in_progress, resolved, closed
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    
    # SLA
    sla_hours: int = 24
    sla_breach: bool = False
    
    created_at: datetime

# Customer Risk Models
class CustomerRiskProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    customer_phone: str
    customer_name: str
    
    # Risk Indicators
    total_orders: int = 0
    return_rate: float = 0.0
    refusal_count: int = 0
    abuse_incidents: int = 0
    dnp_count: int = 0
    
    # Scoring
    risk_score: float = 0.0  # 0-100
    risk_level: str = "low"  # low, medium, high, blocked
    
    # COD Risk
    cod_orders: int = 0
    cod_refusals: int = 0
    cod_risk_score: float = 0.0
    
    # Flags
    is_blocked: bool = False
    block_reason: Optional[str] = None
    flagged_for_abuse: bool = False
    
    # History
    last_order_date: Optional[datetime] = None
    last_issue_date: Optional[datetime] = None
    
    notes: List[str] = []
    
    created_at: datetime
    updated_at: Optional[datetime] = None

# Marketplace Compliance
class MarketplaceHealth(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    marketplace: str  # amazon, flipkart
    asin: Optional[str] = None
    sku: str
    
    # Health Status
    listing_status: str = "active"  # active, suppressed, inactive
    suppression_reason: Optional[str] = None
    health_score: float = 100.0
    
    # Feedback & Reviews
    negative_feedback_count: int = 0
    positive_feedback_count: int = 0
    average_rating: float = 0.0
    
    # Claims & Violations
    az_claims_count: int = 0
    policy_violations: List[Dict] = []
    poa_submissions: List[Dict] = []
    
    # Performance
    safet_claims_filed: int = 0
    safet_claims_approved: int = 0
    safet_approval_rate: float = 0.0
    
    last_checked: datetime
    created_at: datetime
