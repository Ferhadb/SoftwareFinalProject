# Import every model so Base.metadata knows all tables.
from app.models.alert import Alert
from app.models.budget import Budget
from app.models.expense import Category, CategorySource, Expense
from app.models.user import User

__all__ = ["Alert", "Budget", "Category", "CategorySource", "Expense", "User"]
