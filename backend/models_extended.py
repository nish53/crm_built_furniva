from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    TEMPLATE = "template"

class MessageStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

class WhatsAppMessageBase(BaseModel):
    order_id: Optional[str] = None
    customer_phone: str
    message_type: MessageType
    content: str
    media_url: Optional[str] = None
    template_name: Optional[str] = None
    template_params: Optional[List[str]] = None
    status: MessageStatus = MessageStatus.SENT
    is_incoming: bool = False

class WhatsAppMessage(WhatsAppMessageBase):
    model_config = ConfigDict(extra="ignore")
    id: str
    message_id: str
    created_at: datetime
    sent_by: Optional[str] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

class WhatsAppMessageCreate(WhatsAppMessageBase):
    pass

class WhatsAppTemplateBase(BaseModel):
    name: str
    category: str
    language: str = "en"
    template_text: str
    parameters: List[str] = []
    is_active: bool = True

class WhatsAppTemplate(WhatsAppTemplateBase):
    model_config = ConfigDict(extra="ignore")
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class WhatsAppTemplateCreate(WhatsAppTemplateBase):
    pass

class OrderExtended(BaseModel):
    """Extended order model with additional identifiers"""
    master_sku: Optional[str] = None
    fnsku: Optional[str] = None
    asin: Optional[str] = None
    sku: str
    
class AIMessageSuggestion(BaseModel):
    suggestion: str
    context: str
    confidence: float

class ConversationBase(BaseModel):
    customer_phone: str
    customer_name: str
    order_id: Optional[str] = None
    status: str = "active"
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None

class Conversation(ConversationBase):
    model_config = ConfigDict(extra="ignore")
    id: str
    created_at: datetime
    message_count: int = 0
    assigned_to: Optional[str] = None
