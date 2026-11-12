"""
Image upload for profile photos and questionnaire project images.
Stores the file under settings.UPLOADS_DIR (served statically at
/api/uploads, see app/main.py) and hands back a URL the frontend stores
verbatim into the existing profile_image / image_url string fields.
"""
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.deps import get_current_user
from app.core.config import settings
from app.models.models import User
from app.schemas.schemas import ImageUploadOut

router = APIRouter(prefix="/api/media", tags=["media"])

_ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
_MAX_BYTES = 5 * 1024 * 1024


@router.post("/image", response_model=ImageUploadOut)
def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else ""
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Unsupported file type. Please upload a PNG, JPG, WEBP, or GIF image.",
        )

    raw_bytes = file.file.read()
    if len(raw_bytes) > _MAX_BYTES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Image must be 5MB or smaller.")

    upload_dir = os.path.join(settings.UPLOADS_DIR, "images", current_user.id)
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"img-{uuid.uuid4().hex}.{ext}"
    dest_path = os.path.join(upload_dir, filename)
    with open(dest_path, "wb") as f:
        f.write(raw_bytes)

    return ImageUploadOut(url=f"/api/uploads/images/{current_user.id}/{filename}")
