from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from auth import get_current_active_user
from models import User
import uuid
import os
from pathlib import Path
import shutil
from typing import List

router = APIRouter(prefix="/uploads", tags=["uploads"])

# Upload directory
UPLOAD_DIR = Path("/app/backend/uploads")
DAMAGE_IMAGES_DIR = UPLOAD_DIR / "damage_images"

# Create directories if they don't exist
DAMAGE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Allowed image extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".heif"}

def is_allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

@router.post("/damage-image")
async def upload_damage_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a damage image for returns/replacements"""
    
    # Validate file type
    if not is_allowed_file(file.filename):
        raise HTTPException(
            status_code=400, 
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Validate file size (max 5MB)
    file_content = await file.read()
    if len(file_content) > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = DAMAGE_IMAGES_DIR / unique_filename
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Return URL path (relative to API)
    image_url = f"/api/uploads/damage-image/{unique_filename}"
    
    return {
        "message": "Image uploaded successfully",
        "image_url": image_url,
        "filename": unique_filename
    }

@router.post("/damage-images/bulk")
async def upload_damage_images_bulk(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload multiple damage images at once"""
    
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed per upload")
    
    uploaded_urls = []
    errors = []
    
    for file in files:
        try:
            # Validate file type
            if not is_allowed_file(file.filename):
                errors.append({
                    "filename": file.filename,
                    "error": "File type not allowed"
                })
                continue
            
            # Validate file size
            file_content = await file.read()
            if len(file_content) > 5 * 1024 * 1024:
                errors.append({
                    "filename": file.filename,
                    "error": "File size exceeds 5MB"
                })
                continue
            
            # Generate unique filename and save
            file_extension = Path(file.filename).suffix.lower()
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = DAMAGE_IMAGES_DIR / unique_filename
            
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            image_url = f"/api/uploads/damage-image/{unique_filename}"
            uploaded_urls.append({
                "original_filename": file.filename,
                "image_url": image_url,
                "filename": unique_filename
            })
            
        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return {
        "uploaded": len(uploaded_urls),
        "failed": len(errors),
        "images": uploaded_urls,
        "errors": errors
    }

@router.get("/damage-image/{filename}")
async def get_damage_image(filename: str):
    """Retrieve a damage image"""
    file_path = DAMAGE_IMAGES_DIR / filename
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Security: Ensure the file is within the allowed directory
    try:
        file_path.resolve().relative_to(DAMAGE_IMAGES_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return FileResponse(file_path)

@router.delete("/damage-image/{filename}")
async def delete_damage_image(
    filename: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a damage image"""
    file_path = DAMAGE_IMAGES_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    try:
        file_path.unlink()
        return {"message": "Image deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")
