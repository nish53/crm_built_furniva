from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from models import User
from auth import get_current_active_user
from database import get_database
from datetime import datetime, timezone
from typing import List
import uuid
import os
from pathlib import Path

router = APIRouter(prefix="/uploads", tags=["uploads"])

# Create upload directory if it doesn't exist
UPLOAD_DIR = Path("/app/backend/uploads/damage_images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions and max size
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def validate_file(file: UploadFile):
    """Validate file extension and size"""
    # Check extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    return ext

@router.post("/damage-image")
async def upload_damage_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a single damage image"""
    ext = validate_file(file)
    
    # Read and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB")
    
    # Generate unique filename
    filename = f"{uuid.uuid4()}{ext}"
    file_path = UPLOAD_DIR / filename
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Return URL path
    url = f"/api/uploads/damage-image/{filename}"
    
    return {
        "url": url,
        "filename": filename,
        "size": len(content),
        "uploaded_by": current_user.email,
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }

@router.post("/damage-images/bulk")
async def upload_damage_images_bulk(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload multiple damage images (max 10)"""
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed per upload")
    
    uploaded = []
    errors = []
    
    for file in files:
        try:
            ext = validate_file(file)
            content = await file.read()
            
            if len(content) > MAX_FILE_SIZE:
                errors.append({"filename": file.filename, "error": "File too large"})
                continue
            
            filename = f"{uuid.uuid4()}{ext}"
            file_path = UPLOAD_DIR / filename
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            uploaded.append({
                "url": f"/api/uploads/damage-image/{filename}",
                "filename": filename,
                "original_name": file.filename,
                "size": len(content)
            })
        except HTTPException as e:
            errors.append({"filename": file.filename, "error": e.detail})
        except Exception as e:
            errors.append({"filename": file.filename, "error": str(e)})
    
    return {
        "uploaded": uploaded,
        "errors": errors,
        "total_uploaded": len(uploaded),
        "total_errors": len(errors),
        "uploaded_by": current_user.email
    }

@router.get("/damage-image/{filename}")
async def get_damage_image(filename: str):
    """Serve a damage image"""
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Determine media type
    ext = os.path.splitext(filename)[1].lower()
    media_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.heic': 'image/heic'
    }
    media_type = media_types.get(ext, 'application/octet-stream')
    
    return FileResponse(file_path, media_type=media_type)

@router.delete("/damage-image/{filename}")
async def delete_damage_image(
    filename: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a damage image"""
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    os.remove(file_path)
    
    return {
        "message": "Image deleted successfully",
        "filename": filename,
        "deleted_by": current_user.email
    }
