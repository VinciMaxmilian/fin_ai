from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, DbSession
from app.goals.schemas import GoalContribution, GoalCreate, GoalRead, GoalUpdate
from app.goals.service import GoalService

router = APIRouter(prefix="/goals", tags=["Metas"])


@router.get("", response_model=list[GoalRead], summary="Lista as metas")
def list_goals(
    user: CurrentUser, db: DbSession, include_archived: bool = Query(default=False)
) -> list[GoalRead]:
    service = GoalService(db, user.id)
    rows = service.list_goals(include_archived=include_archived)
    return [GoalRead.model_validate(service.to_read(row)) for row in rows]


@router.post("", response_model=GoalRead, status_code=status.HTTP_201_CREATED)
def create_goal(payload: GoalCreate, user: CurrentUser, db: DbSession) -> GoalRead:
    service = GoalService(db, user.id)
    return GoalRead.model_validate(service.to_read(service.create(payload.model_dump())))


@router.get("/{goal_id}", response_model=GoalRead)
def read_goal(goal_id: uuid.UUID, user: CurrentUser, db: DbSession) -> GoalRead:
    service = GoalService(db, user.id)
    return GoalRead.model_validate(service.to_read(service.get(goal_id)))


@router.patch("/{goal_id}", response_model=GoalRead)
def update_goal(
    goal_id: uuid.UUID, payload: GoalUpdate, user: CurrentUser, db: DbSession
) -> GoalRead:
    service = GoalService(db, user.id)
    goal = service.update(goal_id, payload.model_dump(exclude_unset=True))
    return GoalRead.model_validate(service.to_read(goal))


@router.post(
    "/{goal_id}/contributions",
    response_model=GoalRead,
    summary="Registra um aporte ou resgate",
)
def contribute(
    goal_id: uuid.UUID, payload: GoalContribution, user: CurrentUser, db: DbSession
) -> GoalRead:
    service = GoalService(db, user.id)
    return GoalRead.model_validate(service.to_read(service.contribute(goal_id, payload.amount)))


@router.delete("/{goal_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: uuid.UUID, user: CurrentUser, db: DbSession) -> None:
    GoalService(db, user.id).delete(goal_id)
