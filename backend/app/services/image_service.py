import os
import uuid
import hashlib
import time
from typing import Optional, List, BinaryIO
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from PIL import Image as PILImage

from app.core.config import settings
from app.models.image import ImageResource
from app.schemas.image import ImageUpdate, UploadStats


UPLOAD_DIR = "/app/data/uploads"
THUMB_DIR = "/app/data/thumbnails"


class ImageService:

    @staticmethod
    def ensure_dirs():
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        os.makedirs(THUMB_DIR, exist_ok=True)

    @staticmethod
    def allowed_file(filename: str) -> bool:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        allowed = [t.strip() for t in settings.UPLOAD_ALLOWED_TYPES.split(",")]
        return ext in allowed

    @staticmethod
    def _generate_filename(original_name: str) -> str:
        ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else "jpg"
        name_hash = hashlib.md5(f"{uuid.uuid4()}{time.time()}".encode()).hexdigest()[:12]
        return f"{name_hash}.{ext}"

    @staticmethod
    def _create_thumbnail(filepath: str, thumb_path: str) -> bool:
        try:
            img = PILImage.open(filepath)
            img.thumbnail((300, 300), PILImage.LANCZOS)
            img.save(thumb_path, quality=80)
            return True
        except Exception:
            return False

    @staticmethod
    def _compress_image(filepath: str, max_width: int = None, quality: int = None) -> bool:
        if not settings.COMPRESS_ENABLED:
            return False
        try:
            max_w = max_width or settings.COMPRESS_MAX_WIDTH
            q = quality or settings.COMPRESS_QUALITY
            img = PILImage.open(filepath)
            if img.width > max_w:
                ratio = max_w / img.width
                new_size = (max_w, int(img.height * ratio))
                img = img.resize(new_size, PILImage.LANCZOS)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(filepath, quality=q, optimize=True)
            return True
        except Exception:
            return False

    @staticmethod
    def save_upload(file: BinaryIO, original_name: str) -> tuple:
        ImageService.ensure_dirs()
        filename = ImageService._generate_filename(original_name)
        filepath = os.path.join(UPLOAD_DIR, filename)
        content = file.read()
        with open(filepath, "wb") as f:
            f.write(content)
        file_size = len(content)

        ImageService._compress_image(filepath)
        thumb_filename = f"thumb_{filename}"
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

        return filename, file_size, mime_type, width, height, filepath, thumb_path

    @staticmethod
    def create_record(
        db: Session,
        filename: str,
        original_name: str,
        file_size: int,
        mime_type: Optional[str],
        width: Optional[int],
        height: Optional[int],
        thumbnail_path: Optional[str],
        tg_file_id: Optional[str] = None,
        tg_channel_id: Optional[str] = None,
        tg_message_id: Optional[str] = None,
    ) -> ImageResource:
        record = ImageResource(
            filename=filename,
            original_name=original_name,
            file_size=file_size,
            mime_type=mime_type,
            width=width,
            height=height,
            thumbnail_path=thumbnail_path,
            tg_file_id=tg_file_id,
            tg_channel_id=tg_channel_id,
            tg_message_id=tg_message_id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def generate_links(record_id: int, base_url: str = "") -> dict:
        direct_link = f"{base_url}/api/images/file/{record_id}"
        https_link = direct_link
        markdown_link = f"![]({direct_link})"
        bbcode_link = f"[img]{direct_link}[/img]"
        return {
            "direct_link": direct_link,
            "https_link": https_link,
            "markdown_link": markdown_link,
            "bbcode_link": bbcode_link,
        }

    @staticmethod
    def update_links(db: Session, record: ImageResource, base_url: str = ""):
        links = ImageService.generate_links(record.id, base_url)
        for key, value in links.items():
            setattr(record, key, value)
        db.commit()

    @staticmethod
    def get_images(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        category: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> List[ImageResource]:
        query = db.query(ImageResource)
        if category:
            query = query.filter(ImageResource.category == category)
        if keyword:
            query = query.filter(
                ImageResource.original_name.contains(keyword)
                | ImageResource.tags.contains(keyword)
            )
        return query.order_by(desc(ImageResource.uploaded_at)).offset(skip).limit(limit).all()

    @staticmethod
    def get_image(db: Session, image_id: int) -> Optional[ImageResource]:
        return db.query(ImageResource).filter(ImageResource.id == image_id).first()

    @staticmethod
    def update_image(db: Session, image_id: int, data: ImageUpdate) -> Optional[ImageResource]:
        record = db.query(ImageResource).filter(ImageResource.id == image_id).first()
        if not record:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(record, key, value)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def delete_image(db: Session, image_id: int) -> bool:
        record = db.query(ImageResource).filter(ImageResource.id == image_id).first()
        if not record:
            return False
        if record.filename:
            filepath = os.path.join(UPLOAD_DIR, record.filename)
            if os.path.exists(filepath):
                os.remove(filepath)
            thumb_path = os.path.join(THUMB_DIR, f"thumb_{record.filename}")
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
        db.delete(record)
        db.commit()
        return True

    @staticmethod
    def get_stats(db: Session) -> UploadStats:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = today.replace(day=1)

        today_count = db.query(ImageResource).filter(
            ImageResource.uploaded_at >= today
        ).count()
        month_count = db.query(ImageResource).filter(
            ImageResource.uploaded_at >= month_start
        ).count()
        total_count = db.query(ImageResource).count()
        total_size = db.query(func.sum(ImageResource.file_size)).scalar() or 0
        total_views = db.query(func.sum(ImageResource.view_count)).scalar() or 0

        return UploadStats(
            today_upload_count=today_count,
            month_upload_count=month_count,
            total_count=total_count,
            total_size=total_size,
            total_views=total_views,
        )

    @staticmethod
    def increment_view(db: Session, image_id: int):
        record = db.query(ImageResource).filter(ImageResource.id == image_id).first()
        if record:
            record.view_count = (record.view_count or 0) + 1
            db.commit()
