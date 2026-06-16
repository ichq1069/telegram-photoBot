import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import AdminUser
from app.models.bot import BotConfig
from app.schemas.image import ImageResponse, ImageUpdate, ImageUploadResponse, UploadStats
from app.services.image_service import ImageService, UPLOAD_DIR, THUMB_DIR
from app.services.system_service import LogService
from app.services.telegram_adapter import tg_adapter
from PIL import Image as PILImage

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
    bot_id: int = Query(default=None),
    channel_id: str = Query(default=""),
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
    filename = ImageService._generate_filename(file.filename)
    thumb_filename = f"thumb_{filename}"

    # 压缩并创建缩略图（本地仅用于预览）
    ImageService.ensure_dirs()
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(contents)
    ImageService._compress_image(filepath)
    thumb_path = os.path.join(THUMB_DIR, thumb_filename)
    ImageService._create_thumbnail(filepath, thumb_path)

    mime_type = None
    width = None
    height = None
    try:
        img = PILImage.open(filepath)
        width, height = img.size
        mime_type = f"image/{img.format.lower()}" if img.format else None
    except Exception:
        pass

    # 查找机器人配置
    bot = None
    if bot_id:
        bot = db.query(BotConfig).filter(BotConfig.id == bot_id, BotConfig.is_enabled == True).first()
    else:
        bot = db.query(BotConfig).filter(BotConfig.is_enabled == True).first()

    if not bot:
        # 无可用机器人，直接返回本地链接
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        os.makedirs(THUMB_DIR, exist_ok=True)
        record = ImageService.create_record(
            db, filename, file.filename, file_size, mime_type, width, height, thumb_path,
        )
        forwarded_host = request.headers.get("host", "") if request else ""
        forwarded_proto = request.headers.get("x-forwarded-proto", "http") if request else "http"
        base_url = f"{forwarded_proto}://{forwarded_host}" if forwarded_host else (str(request.base_url).rstrip("/") if request else "")
        ImageService.update_links(db, record, base_url)
        LogService.add_log(db, "upload", f"上传图片: {file.filename} (无机器人)", "WARN", "image_upload")
        return ImageUploadResponse(
            id=record.id, filename=record.filename, file_size=record.file_size,
            direct_link=record.direct_link, https_link=record.https_link,
            markdown_link=record.markdown_link, bbcode_link=record.bbcode_link,
        )

    # 上传到 Telegram 频道
    tg_channel = channel_id or (bot.chat_id if bot.chat_id else "")
    if not tg_channel:
        raise HTTPException(status_code=400, detail="请指定存储频道或配置机器人的 ChatID")

    api_mode = bot.api_mode or "official"
    send_kwargs = {}
    if bot.proxy_url:
        send_kwargs["proxies"] = {"https://": bot.proxy_url}

    # 先通过 file_id 方式发送（已存在的 TG 文件）或重新上传
    tg_file_id = None
    tg_message_id = None
    tg_channel_id = tg_channel

    try:
        from io import BytesIO
        result = await tg_adapter.send_photo(
            bot.bot_token, tg_channel, BytesIO(contents),
            api_mode=api_mode,
            self_build_url=bot.self_build_api_url,
            self_build_key=bot.self_build_api_key,
        )

        if result.get("ok"):
            msg = result.get("result", {})
            tg_message_id = str(msg.get("message_id", ""))
            media = msg.get("photo") or msg.get("document") or msg.get("video")
            if media:
                file_obj = media[-1]
                tg_file_id = file_obj.get("file_id", "")
            else:
                # 尝试从 getMe 获取文件
                pass
        else:
            raise RuntimeError(result.get("description", "TG 上传失败"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Telegram 上传失败: {str(e)}")

    # 生成外链
    base_url = ""
    if request:
        forwarded_host = request.headers.get("host", "")
        forwarded_proto = request.headers.get("x-forwarded-proto", "http")
        if forwarded_host:
            base_url = f"{forwarded_proto}://{forwarded_host}"
        else:
            base_url = str(request.base_url).rstrip("/")

    # 如果 TG 直链不可用（自建API），返回管理后台内链
    direct_link = f"{base_url}/api/images/file/{filename}" if tg_file_id else f"{base_url}/api/images/file/{filename}"
    https_link = direct_link
    markdown_link = f"![]({direct_link})"
    bbcode_link = f"[img]{direct_link}[/img]"

    record = ImageService.create_record(
        db, filename, file.filename, file_size, mime_type, width, height, thumb_path,
        tg_file_id=tg_file_id, tg_channel_id=tg_channel_id, tg_message_id=tg_message_id,
        direct_link=direct_link, https_link=https_link,
        markdown_link=markdown_link, bbcode_link=bbcode_link,
    )

    LogService.add_log(db, "upload", f"上传TG图床: {file.filename} file_id={tg_file_id}", "INFO", "image_upload")

    return ImageUploadResponse(
        id=record.id, filename=record.filename, file_size=record.file_size,
        direct_link=record.direct_link, https_link=record.https_link,
        markdown_link=record.markdown_link, bbcode_link=record.bbcode_link,
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
