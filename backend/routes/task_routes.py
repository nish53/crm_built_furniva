from fastapi import APIRouter, Depends, HTTPException
from models import Task, TaskCreate, TaskStatus, User
from auth import get_current_active_user
from database import get_database
from datetime import datetime, timezone
from typing import List, Optional
import uuid

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=Task)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    task_dict = task_data.model_dump()
    task_dict["id"] = str(uuid.uuid4())
    task_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    task_dict["created_by"] = current_user.id
    if task_dict.get("due_date"):
        task_dict["due_date"] = task_dict["due_date"].isoformat()
    
    await db.tasks.insert_one(task_dict)
    return Task(**task_dict)

@router.get("/", response_model=List[Task])
async def get_tasks(
    status: Optional[TaskStatus] = None,
    assigned_to: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    query = {}
    if status:
        query["status"] = status
    if assigned_to:
        query["assigned_to"] = assigned_to
    
    tasks = await db.tasks.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return tasks

@router.patch("/{task_id}")
async def update_task(
    task_id: str,
    status: Optional[TaskStatus] = None,
    assigned_to: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    update_dict = {}
    if status:
        update_dict["status"] = status
        if status == TaskStatus.COMPLETED:
            update_dict["completed_at"] = datetime.now(timezone.utc).isoformat()
    if assigned_to:
        update_dict["assigned_to"] = assigned_to
    
    result = await db.tasks.update_one({"id": task_id}, {"$set": update_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    return Task(**task)

@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    result = await db.tasks.delete_one({"id": task_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}
