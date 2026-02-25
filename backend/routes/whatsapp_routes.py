from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, UploadFile, File
from models_extended import (
    WhatsAppMessage, WhatsAppMessageCreate, WhatsAppTemplate, 
    WhatsAppTemplateCreate, Conversation, AIMessageSuggestion, MessageStatus
)
from models import User
from auth import get_current_active_user
from database import get_database
from whatsapp_service import whatsapp_service
from ai_service import ai_service
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import uuid
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

WEBHOOK_VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN")

@router.get("/webhook")
async def verify_webhook(request: Request):
    """Verify WhatsApp webhook"""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        return int(challenge)
    else:
        raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/webhook")
async def handle_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db = Depends(get_database)
):
    """Handle incoming WhatsApp messages"""
    try:
        body = await request.json()
        
        if body.get("object") != "whatsapp_business_account":
            return {"status": "ignored"}
        
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                
                if "messages" in value:
                    for message in value["messages"]:
                        background_tasks.add_task(
                            process_incoming_message,
                            message,
                            value.get("contacts", [{}])[0],
                            db
                        )
                
                if "statuses" in value:
                    for status in value["statuses"]:
                        background_tasks.add_task(
                            update_message_status,
                            status,
                            db
                        )
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

async def process_incoming_message(message: Dict, contact: Dict, db):
    """Process incoming WhatsApp message"""
    try:
        phone = contact.get("wa_id")
        name = contact.get("profile", {}).get("name", "Unknown")
        message_type = message.get("type")
        message_id = message.get("id")
        
        content = ""
        media_url = None
        
        if message_type == "text":
            content = message.get("text", {}).get("body", "")
        elif message_type in ["image", "video", "document", "audio"]:
            media_url = message.get(message_type, {}).get("link")
            content = message.get(message_type, {}).get("caption", f"[{message_type}]")
        
        # Save to database
        msg_doc = {
            "id": str(uuid.uuid4()),
            "message_id": message_id,
            "customer_phone": phone,
            "message_type": message_type,
            "content": content,
            "media_url": media_url,
            "status": "delivered",
            "is_incoming": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.whatsapp_messages.insert_one(msg_doc)
        
        # Update or create conversation
        conversation = await db.conversations.find_one({"customer_phone": phone}, {"_id": 0})
        if conversation:
            await db.conversations.update_one(
                {"id": conversation["id"]},
                {
                    "$set": {
                        "last_message": content,
                        "last_message_time": datetime.now(timezone.utc).isoformat()
                    },
                    "$inc": {"message_count": 1}
                }
            )
        else:
            conv_doc = {
                "id": str(uuid.uuid4()),
                "customer_phone": phone,
                "customer_name": name,
                "status": "active",
                "last_message": content,
                "last_message_time": datetime.now(timezone.utc).isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "message_count": 1
            }
            await db.conversations.insert_one(conv_doc)
        
        # Mark as read
        try:
            await whatsapp_service.mark_message_as_read(message_id)
        except:
            pass
            
    except Exception as e:
        logger.error(f"Error processing incoming message: {e}")

async def update_message_status(status: Dict, db):
    """Update message delivery status"""
    try:
        message_id = status.get("id")
        new_status = status.get("status")
        timestamp = datetime.fromtimestamp(status.get("timestamp", 0), tz=timezone.utc)
        
        update_data = {"status": new_status}
        
        if new_status == "delivered":
            update_data["delivered_at"] = timestamp.isoformat()
        elif new_status == "read":
            update_data["read_at"] = timestamp.isoformat()
        
        await db.whatsapp_messages.update_one(
            {"message_id": message_id},
            {"$set": update_data}
        )
    except Exception as e:
        logger.error(f"Error updating message status: {e}")

@router.post("/messages/send")
async def send_message(
    to: str,
    message: str,
    order_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Send a text message"""
    try:
        result = await whatsapp_service.send_text_message(to, message)
        
        msg_doc = {
            "id": str(uuid.uuid4()),
            "message_id": result.get("messages", [{}])[0].get("id", ""),
            "customer_phone": to,
            "message_type": "text",
            "content": message,
            "status": "sent",
            "is_incoming": False,
            "order_id": order_id,
            "sent_by": current_user.id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.whatsapp_messages.insert_one(msg_doc)
        
        return {"success": True, "message_id": msg_doc["message_id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/messages/send-media")
async def send_media(
    to: str,
    media_type: str,
    media_url: str,
    caption: Optional[str] = None,
    order_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Send media (image, video, document)"""
    try:
        result = await whatsapp_service.send_media_message(to, media_type, media_url, caption)
        
        msg_doc = {
            "id": str(uuid.uuid4()),
            "message_id": result.get("messages", [{}])[0].get("id", ""),
            "customer_phone": to,
            "message_type": media_type,
            "content": caption or f"[{media_type}]",
            "media_url": media_url,
            "status": "sent",
            "is_incoming": False,
            "order_id": order_id,
            "sent_by": current_user.id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.whatsapp_messages.insert_one(msg_doc)
        
        return {"success": True, "message_id": msg_doc["message_id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/messages/send-template")
async def send_template(
    to: str,
    template_name: str,
    parameters: List[str],
    language: str = "en",
    order_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Send a template message"""
    try:
        result = await whatsapp_service.send_template_message(to, template_name, language, parameters)
        
        msg_doc = {
            "id": str(uuid.uuid4()),
            "message_id": result.get("messages", [{}])[0].get("id", ""),
            "customer_phone": to,
            "message_type": "template",
            "content": f"Template: {template_name}",
            "template_name": template_name,
            "template_params": parameters,
            "status": "sent",
            "is_incoming": False,
            "order_id": order_id,
            "sent_by": current_user.id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.whatsapp_messages.insert_one(msg_doc)
        
        return {"success": True, "message_id": msg_doc["message_id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations")
async def get_conversations(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get all conversations"""
    query = {}
    if status:
        query["status"] = status
    
    conversations = await db.conversations.find(query, {"_id": 0}).sort("last_message_time", -1).to_list(100)
    return conversations

@router.get("/conversations/{phone}")
async def get_conversation(
    phone: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get conversation with message history"""
    conversation = await db.conversations.find_one({"customer_phone": phone}, {"_id": 0})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = await db.whatsapp_messages.find(
        {"customer_phone": phone},
        {"_id": 0}
    ).sort("created_at", 1).to_list(1000)
    
    return {
        "conversation": conversation,
        "messages": messages
    }

@router.post("/ai/suggest-message")
async def suggest_message(
    context: str,
    message_type: str = "general",
    order_id: Optional[str] = None,
    phone: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get AI-powered message suggestion"""
    try:
        order_details = None
        if order_id:
            order = await db.orders.find_one({"id": order_id}, {"_id": 0})
            order_details = order
        
        conversation_history = None
        if phone:
            messages = await db.whatsapp_messages.find(
                {"customer_phone": phone},
                {"_id": 0}
            ).sort("created_at", -1).limit(5).to_list(5)
            conversation_history = messages
        
        suggestion = await ai_service.generate_message_suggestion(
            context=context,
            order_details=order_details,
            conversation_history=conversation_history,
            message_type=message_type
        )
        
        return {"suggestion": suggestion, "context": context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/templates")
async def create_template(
    template: WhatsAppTemplateCreate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Create a message template"""
    template_dict = template.model_dump()
    template_dict["id"] = str(uuid.uuid4())
    template_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.whatsapp_templates.insert_one(template_dict)
    return WhatsAppTemplate(**template_dict)

@router.get("/templates")
async def get_templates(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get all templates"""
    templates = await db.whatsapp_templates.find({"is_active": True}, {"_id": 0}).to_list(100)
    return templates

@router.get("/messages/history/{phone}")
async def get_message_history(
    phone: str,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get message history for a phone number"""
    messages = await db.whatsapp_messages.find(
        {"customer_phone": phone},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    messages.reverse()
    return messages
