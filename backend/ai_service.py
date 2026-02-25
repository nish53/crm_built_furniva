import os
from emergentintegrations.llm.chat import LlmChat, UserMessage
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

EMERGENT_LLM_KEY = os.getenv("EMERGENT_LLM_KEY")

class AIMessageService:
    def __init__(self):
        self.api_key = EMERGENT_LLM_KEY
        
    async def generate_message_suggestion(self, 
                                         context: str,
                                         order_details: Optional[Dict[str, Any]] = None,
                                         conversation_history: Optional[list] = None,
                                         message_type: str = "general") -> str:
        """Generate AI-powered message suggestions based on context"""
        
        system_message = """You are a professional customer service assistant for an e-commerce furniture company. 
Generate helpful, friendly, and concise WhatsApp messages for customers. 
Use a warm, professional tone. Keep messages brief and actionable.
Include relevant order details when provided."""
        
        # Build context for AI
        prompt_parts = []
        
        if message_type == "dispatch_confirmation":
            prompt_parts.append("Generate a dispatch confirmation message")
        elif message_type == "delivery_confirmation":
            prompt_parts.append("Generate a delivery confirmation call message")
        elif message_type == "installation_inquiry":
            prompt_parts.append("Generate a message asking about installation preference (DIY or paid assembly)")
        elif message_type == "follow_up":
            prompt_parts.append("Generate a follow-up message after delivery")
        else:
            prompt_parts.append("Generate an appropriate customer service message")
        
        if order_details:
            prompt_parts.append(f"\nOrder Details:")
            prompt_parts.append(f"- Order Number: {order_details.get('order_number', 'N/A')}")
            prompt_parts.append(f"- Product: {order_details.get('product_name', 'N/A')}")
            prompt_parts.append(f"- Customer: {order_details.get('customer_name', 'N/A')}")
            if order_details.get('tracking_number'):
                prompt_parts.append(f"- Tracking: {order_details.get('tracking_number')}")
        
        if context:
            prompt_parts.append(f"\nAdditional Context: {context}")
        
        if conversation_history:
            prompt_parts.append(f"\nRecent conversation:")
            for msg in conversation_history[-3:]:
                sender = "Customer" if msg.get('is_incoming') else "Us"
                prompt_parts.append(f"{sender}: {msg.get('content', '')}")
        
        prompt_parts.append("\nGenerate ONLY the message text, no explanations. Keep it under 160 characters if possible.")
        
        user_message = UserMessage(text="\n".join(prompt_parts))
        
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"msg_gen_{datetime.now().timestamp()}",
                system_message=system_message
            ).with_model("anthropic", "claude-sonnet-4-5-20250929")
            
            response = await chat.send_message(user_message)
            return response.strip()
        except Exception as e:
            logger.error(f"AI message generation failed: {e}")
            return self._get_fallback_message(message_type, order_details)
    
    def _get_fallback_message(self, message_type: str, order_details: Optional[Dict[str, Any]] = None) -> str:
        """Provide fallback messages if AI fails"""
        fallbacks = {
            "dispatch_confirmation": f"Hi! Your order {order_details.get('order_number', '')} has been dispatched. We'll call you before delivery to confirm timing.",
            "delivery_confirmation": f"Hello! We're calling to confirm delivery timing for your order {order_details.get('order_number', '')}. When would be convenient for you?",
            "installation_inquiry": "Hi! For your furniture assembly, would you prefer DIY installation or paid carpenter assistance?",
            "follow_up": "Hello! We hope you received your order. How was your experience? We'd love your feedback!",
            "general": "Hello! How can we help you today?"
        }
        return fallbacks.get(message_type, fallbacks["general"])
    
    async def analyze_customer_sentiment(self, message: str) -> Dict[str, Any]:
        """Analyze customer message sentiment"""
        system_message = """Analyze the sentiment of customer messages. 
Respond with ONLY a JSON object with: {"sentiment": "positive|neutral|negative", "urgency": "low|medium|high", "requires_action": true|false}"""
        
        user_message = UserMessage(text=f"Analyze this customer message: {message}")
        
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"sentiment_{datetime.now().timestamp()}",
                system_message=system_message
            ).with_model("anthropic", "claude-sonnet-4-5-20250929")
            
            response = await chat.send_message(user_message)
            import json
            return json.loads(response)
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {"sentiment": "neutral", "urgency": "medium", "requires_action": True}

ai_service = AIMessageService()
