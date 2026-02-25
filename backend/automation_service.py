import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import logging
import asyncio
from whatsapp_service import whatsapp_service
from ai_service import ai_service

logger = logging.getLogger(__name__)

class AutomationService:
    """Handles automated customer journey WhatsApp notifications"""
    
    def __init__(self):
        self.enabled = True
    
    async def trigger_order_confirmation(self, order: Dict[str, Any], db) -> bool:
        """Send order confirmation message"""
        try:
            template_params = [
                order.get('customer_name', 'Customer'),
                order.get('order_number', ''),
                order.get('product_name', ''),
                str(order.get('price', 0))
            ]
            
            # Generate AI message if template not available
            message = await ai_service.generate_message_suggestion(
                context=f"Order confirmed",
                order_details=order,
                message_type="general"
            )
            
            # Send message
            result = await whatsapp_service.send_text_message(
                to=order.get('phone', ''),
                message=message
            )
            
            # Log automation
            await self._log_automation(db, order, 'order_confirmation', message, 'sent')
            return True
            
        except Exception as e:
            logger.error(f"Order confirmation automation failed: {e}")
            await self._log_automation(db, order, 'order_confirmation', '', 'failed')
            return False
    
    async def trigger_dispatch_call_reminder(self, order: Dict[str, Any], db) -> bool:
        """Send DC1 (Dispatch Call) reminder"""
        try:
            message = await ai_service.generate_message_suggestion(
                context="Need to call customer before dispatch to confirm delivery timing and installation preference",
                order_details=order,
                message_type="delivery_confirmation"
            )
            
            result = await whatsapp_service.send_text_message(
                to=order.get('phone', ''),
                message=message
            )
            
            # Update order status
            await db.orders.update_one(
                {"id": order['id']},
                {"$set": {"cp_sent": True}}
            )
            
            await self._log_automation(db, order, 'dispatch_call_reminder', message, 'sent')
            return True
            
        except Exception as e:
            logger.error(f"Dispatch call reminder failed: {e}")
            await self._log_automation(db, order, 'dispatch_call_reminder', '', 'failed')
            return False
    
    async def trigger_dispatch_notification(self, order: Dict[str, Any], db) -> bool:
        """Send dispatch notification with tracking"""
        try:
            tracking = order.get('tracking_number', 'Will be updated soon')
            courier = order.get('courier_partner', 'our logistics partner')
            
            message = f"""Hi {order.get('customer_name')}! 📦

Great news! Your order {order.get('order_number')} has been dispatched via {courier}.

🚚 Tracking: {tracking}
📅 Expected delivery: 2-3 business days

We'll call you before delivery to confirm timing. For assembly instructions, reply 'HELP'.

Thank you for choosing us!"""
            
            result = await whatsapp_service.send_text_message(
                to=order.get('phone', ''),
                message=message
            )
            
            await self._log_automation(db, order, 'dispatch_notification', message, 'sent')
            return True
            
        except Exception as e:
            logger.error(f"Dispatch notification failed: {e}")
            await self._log_automation(db, order, 'dispatch_notification', '', 'failed')
            return False
    
    async def trigger_installation_inquiry(self, order: Dict[str, Any], db) -> bool:
        """Ask about installation preference"""
        try:
            message = await ai_service.generate_message_suggestion(
                context="Ask if customer wants DIY assembly or paid carpenter assistance",
                order_details=order,
                message_type="installation_inquiry"
            )
            
            result = await whatsapp_service.send_text_message(
                to=order.get('phone', ''),
                message=message
            )
            
            await self._log_automation(db, order, 'installation_inquiry', message, 'sent')
            return True
            
        except Exception as e:
            logger.error(f"Installation inquiry failed: {e}")
            await self._log_automation(db, order, 'installation_inquiry', '', 'failed')
            return False
    
    async def trigger_delivery_confirmation(self, order: Dict[str, Any], db) -> bool:
        """Send delivery confirmation and thank you message"""
        try:
            message = f"""Hi {order.get('customer_name')}! ✅

Your order {order.get('order_number')} has been delivered!

We hope you love your {order.get('product_name')}. 

🔧 Need assembly help? Reply 'ASSEMBLY'
⭐ Happy with your purchase? We'd love your review!

Reply 'REVIEW' to share your feedback.

Thank you for choosing us!"""
            
            result = await whatsapp_service.send_text_message(
                to=order.get('phone', ''),
                message=message
            )
            
            await self._log_automation(db, order, 'delivery_confirmation', message, 'sent')
            return True
            
        except Exception as e:
            logger.error(f"Delivery confirmation failed: {e}")
            await self._log_automation(db, order, 'delivery_confirmation', '', 'failed')
            return False
    
    async def trigger_review_request(self, order: Dict[str, Any], db) -> bool:
        """Request customer review after 3 days of delivery"""
        try:
            message = await ai_service.generate_message_suggestion(
                context="Request honest review and feedback about product and service",
                order_details=order,
                message_type="follow_up"
            )
            
            result = await whatsapp_service.send_text_message(
                to=order.get('phone', ''),
                message=message
            )
            
            # Mark review requested
            await db.orders.update_one(
                {"id": order['id']},
                {"$set": {"review_conf": True}}
            )
            
            await self._log_automation(db, order, 'review_request', message, 'sent')
            return True
            
        except Exception as e:
            logger.error(f"Review request failed: {e}")
            await self._log_automation(db, order, 'review_request', '', 'failed')
            return False
    
    async def trigger_dnp_followup(self, order: Dict[str, Any], attempt: int, db) -> bool:
        """Send DNP (Did Not Pick) follow-up messages"""
        try:
            if attempt == 1:
                message = f"Hi {order.get('customer_name')}, we tried calling about your order {order.get('order_number')}. Please call us back or reply here. Thanks!"
            elif attempt == 2:
                message = f"Hi, this is our 2nd attempt to reach you for order {order.get('order_number')}. Please confirm if you still want this order. Reply YES to confirm."
            else:
                message = f"Final reminder: Order {order.get('order_number')} will be cancelled if we don't hear from you within 24 hours. Please confirm."
            
            result = await whatsapp_service.send_text_message(
                to=order.get('phone', ''),
                message=message
            )
            
            # Update DNP confirmation status
            field = f"dnp{attempt}_conf"
            await db.orders.update_one(
                {"id": order['id']},
                {"$set": {field: True}}
            )
            
            await self._log_automation(db, order, f'dnp_followup_{attempt}', message, 'sent')
            return True
            
        except Exception as e:
            logger.error(f"DNP followup {attempt} failed: {e}")
            await self._log_automation(db, order, f'dnp_followup_{attempt}', '', 'failed')
            return False
    
    async def _log_automation(self, db, order: Dict[str, Any], automation_type: str, message: str, status: str):
        """Log automation activity"""
        try:
            log_doc = {
                "id": str(datetime.now().timestamp()),
                "order_id": order.get('id'),
                "order_number": order.get('order_number'),
                "customer_phone": order.get('phone'),
                "automation_type": automation_type,
                "message": message,
                "status": status,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.automation_logs.insert_one(log_doc)
        except Exception as e:
            logger.error(f"Failed to log automation: {e}")
    
    async def process_order_status_change(self, order_id: str, old_status: str, new_status: str, db):
        """Trigger appropriate automations when order status changes"""
        try:
            order = await db.orders.find_one({"id": order_id}, {"_id": 0})
            if not order:
                return
            
            # Confirmed -> Send dispatch call reminder
            if new_status == "confirmed" and old_status == "pending":
                await self.trigger_order_confirmation(order, db)
                # Schedule DC1 for next day
                await self.schedule_automation(order_id, "dispatch_call_reminder", hours=24, db=db)
            
            # Dispatched -> Send tracking info
            elif new_status == "dispatched":
                await self.trigger_dispatch_notification(order, db)
                # Ask about installation after 1 day
                await self.schedule_automation(order_id, "installation_inquiry", hours=24, db=db)
            
            # Delivered -> Thank you + review request schedule
            elif new_status == "delivered":
                await self.trigger_delivery_confirmation(order, db)
                # Request review after 3 days
                await self.schedule_automation(order_id, "review_request", hours=72, db=db)
            
        except Exception as e:
            logger.error(f"Process order status change failed: {e}")
    
    async def schedule_automation(self, order_id: str, automation_type: str, hours: int, db):
        """Schedule automation for future execution"""
        try:
            scheduled_time = datetime.now(timezone.utc) + timedelta(hours=hours)
            
            schedule_doc = {
                "id": str(datetime.now().timestamp()),
                "order_id": order_id,
                "automation_type": automation_type,
                "scheduled_time": scheduled_time.isoformat(),
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.automation_schedule.insert_one(schedule_doc)
            logger.info(f"Scheduled {automation_type} for order {order_id} at {scheduled_time}")
            
        except Exception as e:
            logger.error(f"Schedule automation failed: {e}")
    
    async def process_scheduled_automations(self, db):
        """Process pending scheduled automations"""
        try:
            now = datetime.now(timezone.utc).isoformat()
            
            pending = await db.automation_schedule.find({
                "status": "pending",
                "scheduled_time": {"$lte": now}
            }, {"_id": 0}).to_list(100)
            
            for schedule in pending:
                order = await db.orders.find_one({"id": schedule['order_id']}, {"_id": 0})
                if not order:
                    continue
                
                automation_type = schedule['automation_type']
                
                # Execute appropriate automation
                success = False
                if automation_type == "dispatch_call_reminder":
                    success = await self.trigger_dispatch_call_reminder(order, db)
                elif automation_type == "installation_inquiry":
                    success = await self.trigger_installation_inquiry(order, db)
                elif automation_type == "review_request":
                    success = await self.trigger_review_request(order, db)
                
                # Update schedule status
                await db.automation_schedule.update_one(
                    {"id": schedule['id']},
                    {"$set": {
                        "status": "completed" if success else "failed",
                        "executed_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
            
            return len(pending)
            
        except Exception as e:
            logger.error(f"Process scheduled automations failed: {e}")
            return 0

automation_service = AutomationService()
