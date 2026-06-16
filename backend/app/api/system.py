from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import AdminUser
from app.schemas.system import (
    SystemConfigResponse,
    SystemConfigUpdate,
    LogResponse,
    LogListResponse,
    DatabaseStatus,
    SystemStats,
)
from app.services.system_service import LogService, ConfigService, MonitorService, DatabaseSyncService

router = APIRouter(prefix="/api/system", tags=["系统管理"])


@router.get("/stats", response_model=SystemStats)
def get_stats(
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    return MonitorService.get_system_stats(db)


@router.get("/configs", response_model=List[SystemConfigResponse])
def list_configs(
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    return ConfigService.get_all_configs(db)


@router.put("/configs/{config_key}")
def update_config(
    config_key: str,
    data: SystemConfigUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    ConfigService.set_config(db, config_key, data.config_value)
    return {"message": "配置更新成功"}


@router.get("/logs", response_model=LogListResponse)
def get_logs(
    log_type: Optional[str] = None,
    level: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    logs, total = LogService.get_logs(
        db, log_type=log_type, level=level, keyword=keyword,
        page=page, page_size=page_size,
    )
    return LogListResponse(
        items=logs,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/database/status", response_model=DatabaseStatus)
def get_database_status(
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    return DatabaseSyncService.get_status(db)


@router.post("/database/sync")
def sync_database(
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    try:
        DatabaseSyncService.sync_to_mysql(db)
        return {"message": "同步完成"}
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


@router.post("/database/switch/{target}")
def switch_database(
    target: str,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    try:
        DatabaseSyncService.switch_database(db, target)
        return {"message": f"已切换到{target}数据库"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
