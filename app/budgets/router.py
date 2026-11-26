from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.auth.security import get_current_user
from app.budgets.schemas import (
    BudgetResponse,
    BudgetStatusResponse,
    BudgetUpsertRequest,
)
from app.budgets.service import (
    BudgetNotFoundError,
    BudgetService,
    get_budget_service,
)
from app.models import Budget, Category, User

router = APIRouter(prefix="/budgets", tags=["Budgets"])
alerts_router = APIRouter(prefix="/alerts", tags=["Alerts"])

MonthFilter = Annotated[
    str | None,
    Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
]


@router.get("", response_model=list[BudgetResponse])
def list_budgets(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[BudgetService, Depends(get_budget_service)],
) -> list[Budget]:
    return service.list(current_user.id)


@router.get("/status", response_model=list[BudgetStatusResponse])
def get_budget_status(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[BudgetService, Depends(get_budget_service)],
    month: MonthFilter = None,
) -> list[BudgetStatusResponse]:
    return service.status(current_user.id, month)


@router.put("/{category}", response_model=BudgetResponse)
def upsert_budget(
    category: Category,
    request: BudgetUpsertRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[BudgetService, Depends(get_budget_service)],
) -> Budget:
    return service.upsert(current_user.id, category, request.monthly_limit)


@router.delete("/{category}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    category: Category,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[BudgetService, Depends(get_budget_service)],
) -> Response:
    try:
        service.delete(current_user.id, category)
    except BudgetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
