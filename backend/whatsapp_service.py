import os
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

WHATSAPP_API_URL = "https://graph.facebook.com/v21.0"
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

class WhatsAppService:
    def __init__(self):
        self.api_url = WHATSAPP_API_URL
        self.token = WHATSAPP_API_TOKEN
        self.phone_number_id = WHATSAPP_PHONE_NUMBER_ID
        
    async def send_text_message(self, to: str, message: str) -> Dict[str, Any]:
        """Send a text message via WhatsApp Business API"""
        url = f"{self.api_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            raise
    
    async def send_media_message(self, to: str, media_type: str, media_url: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """Send media (image, video, document) via WhatsApp"""
        url = f"{self.api_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        media_content = {"link": media_url}
        if caption:
            media_content["caption"] = caption
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": media_type,
            media_type: media_content
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to send WhatsApp media: {e}")
            raise
    
    async def send_template_message(self, to: str, template_name: str, language: str, parameters: List[str]) -> Dict[str, Any]:
        """Send a template message via WhatsApp"""
        url = f"{self.api_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        components = []
        if parameters:
            components.append({
                "type": "body",
                "parameters": [{"type": "text", "text": param} for param in parameters]
            })
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
                "components": components
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to send WhatsApp template: {e}")
            raise
    
    async def upload_media(self, media_file_path: str, media_type: str) -> str:
        """Upload media to WhatsApp and get media ID"""
        url = f"{self.api_url}/{self.phone_number_id}/media"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                with open(media_file_path, 'rb') as f:
                    files = {'file': f}
                    data = {'messaging_product': 'whatsapp', 'type': media_type}
                    response = await client.post(url, files=files, data=data, headers=headers)
                    response.raise_for_status()
                    return response.json().get('id')
        except Exception as e:
            logger.error(f"Failed to upload media: {e}")
            raise
    
    async def mark_message_as_read(self, message_id: str) -> Dict[str, Any]:
        """Mark a message as read"""
        url = f"{self.api_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to mark message as read: {e}")
            raise

whatsapp_service = WhatsAppService()
