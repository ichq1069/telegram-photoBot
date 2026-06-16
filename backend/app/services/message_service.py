from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.message import MessageTemplate
from app.schemas.message import MessageTemplateCreate, MessageTemplateUpdate


class MessageService:

    @staticmethod
    def get_templates(
        db: Session, bot_id: Optional[int] = None, skip: int = 0, limit: int = 100
    ) -> List[MessageTemplate]:
        query = db.query(MessageTemplate)
        if bot_id:
            query = query.filter(MessageTemplate.bot_id == bot_id)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_template(db: Session, template_id: int) -> Optional[MessageTemplate]:
        return db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()

    @staticmethod
    def create_template(db: Session, data: MessageTemplateCreate) -> MessageTemplate:
        template = MessageTemplate(**data.model_dump())
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def update_template(
        db: Session, template_id: int, data: MessageTemplateUpdate
    ) -> Optional[MessageTemplate]:
        template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
        if not template:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(template, key, value)
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def delete_template(db: Session, template_id: int) -> bool:
        template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
        if not template:
            return False
        db.delete(template)
        db.commit()
        return True
