from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum

from core.mixins import FarmCreateView, FarmDeleteView, FarmListView, FarmUpdateView

from .forms import MilkRecordForm
from .models import MilkRecord

REVENUE = ExpressionWrapper(
    F("liters") * F("rate_per_liter"), output_field=DecimalField(max_digits=14, decimal_places=2)
)


class MilkListView(FarmListView):
    model = MilkRecord
    title = "Milk production"
    columns = (
        ("Date", "date", "date"),
        ("Session", "session", ""),
        ("Animal", "animal_display", ""),
        ("Liters", "liters", "liters"),
        ("Rate / L", "rate_per_liter", "money"),
        ("Amount", "amount", "money"),
    )
    search_fields = ("animal__tag_number", "animal__name", "notes")
    date_field = "date"
    choice_field = "session"
    choice_label = "Session"
    select_related = ("animal",)

    def get_totals(self, qs):
        agg = qs.aggregate(liters_total=Sum("liters"), revenue_total=Sum(REVENUE))
        return [
            ("Total milk", f"{(agg['liters_total'] or Decimal('0')):,.2f} L"),
            ("Milk sales", self.money(agg["revenue_total"] or Decimal("0"))),
        ]


class MilkCreateView(FarmCreateView):
    model = MilkRecord
    form_class = MilkRecordForm


class MilkUpdateView(FarmUpdateView):
    model = MilkRecord
    form_class = MilkRecordForm


class MilkDeleteView(FarmDeleteView):
    model = MilkRecord
