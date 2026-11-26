from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.views.generic import TemplateView

from animals.models import Animal
from core.utils import today
from expenses.models import Expense
from milk.models import MilkRecord
from reports.services import month_series, month_summary


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        now = today()
        summary = month_summary(user, now.year, now.month)
        series = month_series(user, now.year, now.month, 6)

        animals = Animal.objects.filter(owner=user).exclude(status__in=Animal.INACTIVE_STATUSES)
        today_liters = (
            MilkRecord.objects.filter(owner=user, date=now).aggregate(total=Sum("liters"))["total"] or 0
        )
        ctx.update(
            s=summary,
            series=series,
            animals_active=animals.count(),
            animals_lactating=animals.filter(status="lactating").count(),
            today_liters=today_liters,
            recent_milk=MilkRecord.objects.filter(owner=user).select_related("animal")[:5],
            recent_expenses=Expense.objects.filter(owner=user)[:5],
            chart={
                "labels": [r["label"] for r in series],
                "income": [float(r["income"]) for r in series],
                "expense": [float(r["expense"]) for r in series],
                "cat_labels": [r["label"] for r in summary["expense_rows"]],
                "cat_values": [float(r["total"]) for r in summary["expense_rows"]],
            },
        )
        return ctx
