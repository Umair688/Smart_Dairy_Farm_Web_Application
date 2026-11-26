from decimal import Decimal

from django.db.models import Sum

from core.mixins import FarmCreateView, FarmDeleteView, FarmListView, FarmUpdateView

from .forms import IncomeForm
from .models import Income


class IncomeListView(FarmListView):
    model = Income
    title = "Other income"
    columns = (
        ("Date", "date", "date"),
        ("Source", "source", ""),
        ("Description", "description", ""),
        ("Amount", "amount", "money"),
    )
    search_fields = ("description",)
    date_field = "date"
    choice_field = "source"
    choice_label = "Source"

    def get_totals(self, qs):
        total = qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")
        return [("Total other income", self.money(total))]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["hint"] = "Daily milk sales are counted automatically from your Milk records - don't add them here."
        return ctx


class IncomeCreateView(FarmCreateView):
    model = Income
    form_class = IncomeForm


class IncomeUpdateView(FarmUpdateView):
    model = Income
    form_class = IncomeForm


class IncomeDeleteView(FarmDeleteView):
    model = Income
