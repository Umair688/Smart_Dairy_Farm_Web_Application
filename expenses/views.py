from decimal import Decimal

from django.db.models import Sum

from core.mixins import FarmCreateView, FarmDeleteView, FarmListView, FarmUpdateView

from .forms import ExpenseForm
from .models import Expense


class ExpenseListView(FarmListView):
    model = Expense
    title = "Expenses"
    columns = (
        ("Date", "date", "date"),
        ("Category", "category", ""),
        ("Description", "description", ""),
        ("Animal", "animal_display", ""),
        ("Amount", "amount", "money"),
    )
    search_fields = ("description", "animal__tag_number", "animal__name")
    date_field = "date"
    choice_field = "category"
    choice_label = "Category"
    select_related = ("animal",)

    def get_totals(self, qs):
        total = qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")
        return [("Total expenses", self.money(total))]


class ExpenseCreateView(FarmCreateView):
    model = Expense
    form_class = ExpenseForm


class ExpenseUpdateView(FarmUpdateView):
    model = Expense
    form_class = ExpenseForm


class ExpenseDeleteView(FarmDeleteView):
    model = Expense
