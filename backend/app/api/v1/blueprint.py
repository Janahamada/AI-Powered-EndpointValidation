"""Blueprint / Policies route: the assurance baseline the engine validates against."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.db_models import User
from app.schemas.blueprint import BlueprintView
from app.services import blueprint_view_service

router = APIRouter(prefix="/blueprint", tags=["blueprint"])


@router.get("", response_model=BlueprintView)
def get_blueprint(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> BlueprintView:
    return blueprint_view_service.build_blueprint_view(db)
