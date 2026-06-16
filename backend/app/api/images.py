import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import AdminUser
from app.schemas.image import ImageResponse, ImageUpdate, ImageUploadResponse, UploadStats
from app.services.image_service import ImageService
from app.services.system_service import LogService

router = APIRouter(prefix="/api/images", tags=["图床管理"])


@router.get("", response_model=List[ImageResponse])
def list_images(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    return ImageService.get_images(db, skip, limit, category, keyword)


@router.get("/stats", response_model=UploadStats)
def get_stats(
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    return ImageService.get_stats(db)


@router.get("/{image_id}", response_model=ImageResponse)
def get_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    record = ImageService.get_image(db, image_id)
    if not record:
        raise HTTPException(status_code=404, detail="图片不存在")
    return record


@router.put("/{image_id}", response_model=ImageResponse)
def update_image(
    image_id: int,
    data: ImageUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    record = ImageService.update_image(db, image_id, data)
    if not record:
        raise HTTPException(status_code=404, detail="图片不存在")
    return record


@router.delete("/{image_id}")
def delete_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    if not ImageService.delete_image(db, image_id):
        raise HTTPException(status_code=404, detail="图片不存在")
    return {"message": "删除成功"}


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
    request: Request = None,
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="未选择文件")

    if not ImageService.allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="不支持的文件格式")

    contents = await file.read()
    file_size = len(contents)
    max_size = settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(status_code=400, detail=f"文件大小超过{settings.UPLOAD_MAX_SIZE_MB}MB限制")

    from io import BytesIO
    filename, file_size, mime_type, width, height, filepath, thumb_path = (
        ImageService.save_upload(BytesIO(contents), file.filename)
    )

    record = ImageService.create_record(
        db, filename, file.filename, file_size, mime_type, width, height, thumb_path
    )

    forwarded_host = request.headers.get("host", "")
    forwarded_proto = request.headers.get("x-forwarded-proto", "http")
    if forwarded_host:
        base_url = f"{forwarded_proto}://{forwarded_host}"
    else:
        base_url = str(request.base_url).rstrip("/")
    ImageService.update_links(db, record, base_url)

    LogService.add_log(db, "upload", f"上传图片: {file.filename}", "INFO", "image_upload")

    return ImageUploadResponse(
        id=record.id,
        filename=record.filename,
        file_size=record.file_size,
        direct_link=record.direct_link,
        https_link=record.https_link,
        markdown_link=record.markdown_link,
        bbcode_link=record.bbcode_link,
    )


@router.get("/file/{image_id}")
def serve_image(
    image_id: int,
    db: Session = Depends(get_db),
):
    record = ImageService.get_image(db, image_id)
    if not record:
        raise HTTPException(status_code=404, detail="图片不存在")

    if not record.is_public:
        raise HTTPException(status_code=403, detail="图片未公开")

    if record.expire_time:
        from datetime import datetime
        if datetime.utcnow() > record.expire_time:
            raise HTTPException(status_code=410, detail="图片链接已过期")

    ImageService.increment_view(db, image_id)

    filepath = os.path.join("/app/data/uploads", record.filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="图片文件不存在")

    media_type = record.mime_type or "application/octet-stream"
    return FileResponse(filepath, media_type=media_type)


@router.get("/file/{image_id}/thumb")
def serve_thumbnail(
    image_id: int,
    db: Session = Depends(get_db),
):
    record = ImageService.get_image(db, image_id)
    if not record:
        raise HTTPException(status_code=404, detail="图片不存在")

    thumb_filename = f"thumb_{record.filename}"
    thumb_path = os.path.join("/app/data/thumbnails", thumb_filename)
    if not os.path.exists(thumb_path):
        filepath = os.path.join("/app/data/uploads", record.filename)
        if os.path.exists(filepath):
            return FileResponse(filepath)
        raise HTTPException(status_code=404, detail="缩略图不存在")

    return FileResponse(thumb_path)
