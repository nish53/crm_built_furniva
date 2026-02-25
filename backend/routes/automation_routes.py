from fastapi import APIRouter, Depends, BackgroundTasks
from models import User, OrderStatus
from auth import get_current_active_user
from database import get_database
from automation_service import automation_service
from typing import Optional

router = APIRouter(prefix="/automation", tags=["automation"])

@router.post("/trigger/{order_id}")
async def trigger_automation(
    order_id: str,
    automation_type: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Manually trigger an automation for an order"""
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        return {"success": False, "error": "Order not found"}
    
    if automation_type == "order_confirmation":
        background_tasks.add_task(automation_service.trigger_order_confirmation, order, db)
    elif automation_type == "dispatch_call":
        background_tasks.add_task(automation_service.trigger_dispatch_call_reminder, order, db)
    elif automation_type == "dispatch_notification":
        background_tasks.add_task(automation_service.trigger_dispatch_notification, order, db)
    elif automation_type == "installation_inquiry":
        background_tasks.add_task(automation_service.trigger_installation_inquiry, order, db)
    elif automation_type == "delivery_confirmation":
        background_tasks.add_task(automation_service.trigger_delivery_confirmation, order, db)
    elif automation_type == "review_request":
        background_tasks.add_task(automation_service.trigger_review_request, order, db)
    else:
        return {"success": False, "error": "Invalid automation type"}
    
    return {"success": True, "message": f"Automation {automation_type} triggered"}

@router.get("/logs/{order_id}")
async def get_automation_logs(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get automation logs for an order"""
    logs = await db.automation_logs.find(
        {"order_id": order_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return logs

@router.get("/schedule")
async def get_scheduled_automations(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get scheduled automations"""
    query = {}
    if status:
        query["status"] = status
    
    schedules = await db.automation_schedule.find(
        query,
        {"_id": 0}
    ).sort("scheduled_time", 1).to_list(100)
    
    return schedules

@router.post("/process-scheduled")
async def process_scheduled(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Manually trigger processing of scheduled automations"""
    background_tasks.add_task(automation_service.process_scheduled_automations, db)
    return {"success": True, "message": "Processing scheduled automations"}

@router.get("/stats")
async def get_automation_stats(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get automation statistics"""
    total_logs = await db.automation_logs.count_documents({})
    sent = await db.automation_logs.count_documents({"status": "sent"})
    failed = await db.automation_logs.count_documents({"status": "failed"})
    pending_schedules = await db.automation_schedule.count_documents({"status": "pending"})
    
    return {
        "total_automations": total_logs,
        "successful": sent,
        "failed": failed,
        "pending_scheduled": pending_schedules,
        "success_rate": round((sent / total_logs * 100) if total_logs > 0 else 0, 2)
    }
