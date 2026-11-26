from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.auth.security import get_current_user
from app.expenses.schemas import (
    ExpenseCreateRequest,
    ExpenseResponse,
    ExpenseUpdateRequest,
)
from app.expenses.service import (
    ExpenseNotFoundError,
    ExpenseService,
    InvalidExpenseTextError,
    get_expense_service,
)
from app.models import Category, Expense, User

router = APIRouter(prefix="/expenses", tags=["Expenses"])

MonthFilter = Annotated[
    str | None,
    Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
]


@router.post(
    "",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_expense(
    request: ExpenseCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ExpenseService, Depends(get_expense_service)],
) -> Expense:
    try:
        return service.create(current_user.id, request)
    except InvalidExpenseTextError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Expense text could not be parsed",
        ) from exc


@router.get("", response_model=list[ExpenseResponse])
def list_expenses(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ExpenseService, Depends(get_expense_service)],
    month: MonthFilter = None,
    category: Category | None = None,
) -> list[Expense]:
    return service.list(current_user.id, month, category)


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ExpenseService, Depends(get_expense_service)],
) -> Expense:
    try:
        return service.get(current_user.id, expense_id)
    except ExpenseNotFoundError as exc:
        raise _not_found() from exc


@router.patch("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    request: ExpenseUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ExpenseService, Depends(get_expense_service)],
) -> Expense:
    try:
        return service.update(current_user.id, expense_id, request)
    except ExpenseNotFoundError as exc:
        raise _not_found() from exc


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ExpenseService, Depends(get_expense_service)],
) -> Response:
    try:
        service.delete(current_user.id, expense_id)
    except ExpenseNotFoundError as exc:
        raise _not_found() from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Expense not found",
    )
