"""Profit & loss calculations. Pure queries, no HTTP - easy to test and reuse."""
import datetime as dt
from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncMonth

from core.utils import format_money, month_bounds, month_label, month_value, shift_month
from expenses.models import Expense
from income.models import Income
from milk.models import MilkRecord

ZERO = Decimal("0")
CENT = Decimal("0.01")
MILK_REVENUE = ExpressionWrapper(
    F("liters") * F("rate_per_liter"),
    output_field=DecimalField(max_digits=14, decimal_places=2),
)


def _d(value):
    return value if value is not None else ZERO


def _q(value):
    return _d(value).quantize(CENT)


def _pct(part, whole):
    return (part / whole * 100).quantize(Decimal("0.1")) if whole else ZERO


def month_summary(user, year, month):
    """Everything the monthly report needs, for one user and one month."""
    start, end = month_bounds(year, month)
    milk = MilkRecord.objects.filter(owner=user, date__range=(start, end))
    expenses = Expense.objects.filter(owner=user, date__range=(start, end))
    incomes = Income.objects.filter(owner=user, date__range=(start, end))

    milk_agg = milk.aggregate(liters_total=Sum("liters"), revenue_total=Sum(MILK_REVENUE))
    milk_liters = _q(milk_agg["liters_total"])
    milk_revenue = _q(milk_agg["revenue_total"])
    other_income = _q(incomes.aggregate(total=Sum("amount"))["total"])
    total_expense = _q(expenses.aggregate(total=Sum("amount"))["total"])
    total_income = milk_revenue + other_income
    net = total_income - total_expense

    has_data = bool(milk.exists() or expenses.exists() or incomes.exists())
    if not has_data:
        status = "empty"
    elif net > 0:
        status = "profit"
    elif net < 0:
        status = "loss"
    else:
        status = "even"

    # Expense breakdown
    expense_labels = dict(Expense.CATEGORY_CHOICES)
    expense_rows = [
        {
            "label": expense_labels.get(r["category"], r["category"]),
            "key": r["category"],
            "total": _q(r["cat_total"]),
            "pct": _pct(_d(r["cat_total"]), total_expense),
        }
        for r in expenses.values("category").annotate(cat_total=Sum("amount")).order_by("-cat_total")
    ]

    # Income breakdown (milk first, then other sources)
    income_labels = dict(Income.SOURCE_CHOICES)
    income_rows = []
    if milk_revenue:
        income_rows.append({"label": "Milk sales", "total": milk_revenue, "pct": _pct(milk_revenue, total_income)})
    for r in incomes.values("source").annotate(src_total=Sum("amount")).order_by("-src_total"):
        income_rows.append(
            {
                "label": income_labels.get(r["source"], r["source"]),
                "total": _q(r["src_total"]),
                "pct": _pct(_d(r["src_total"]), total_income),
            }
        )

    # Day-by-day figures for charts
    milk_by_day = {
        r["date"]: r
        for r in milk.values("date")
        .annotate(day_liters=Sum("liters"), day_revenue=Sum(MILK_REVENUE))
        .order_by("date")
    }
    income_by_day = {
        r["date"]: r["day_total"]
        for r in incomes.values("date").annotate(day_total=Sum("amount")).order_by("date")
    }
    expense_by_day = {
        r["date"]: r["day_total"]
        for r in expenses.values("date").annotate(day_total=Sum("amount")).order_by("date")
    }
    daily = []
    for i in range((end - start).days + 1):
        day = start + dt.timedelta(days=i)
        m = milk_by_day.get(day)
        daily.append(
            {
                "day": day.day,
                "liters": _d(m["day_liters"]) if m else ZERO,
                "income": (_d(m["day_revenue"]) if m else ZERO) + _d(income_by_day.get(day)),
                "expense": _d(expense_by_day.get(day)),
            }
        )

    top_animals = [
        {
            "tag": r["animal__tag_number"],
            "name": r["animal__name"],
            "liters": _q(r["a_liters"]),
            "revenue": _q(r["a_revenue"]),
        }
        for r in milk.filter(animal__isnull=False)
        .values("animal__tag_number", "animal__name")
        .annotate(a_liters=Sum("liters"), a_revenue=Sum(MILK_REVENUE))
        .order_by("-a_liters")[:5]
    ]

    days_with_milk = milk.values("date").distinct().count()
    avg_daily_liters = (milk_liters / days_with_milk).quantize(CENT) if days_with_milk else ZERO
    revenue_per_liter = (milk_revenue / milk_liters).quantize(CENT) if milk_liters else None
    cost_per_liter = (total_expense / milk_liters).quantize(CENT) if milk_liters else None
    # Milk price needed so that milk sales + other income cover all expenses
    break_even_rate = (
        ((total_expense - other_income) / milk_liters).quantize(CENT) if milk_liters else None
    )
    margin_pct = _pct(net, total_income) if total_income else None

    return {
        "year": year,
        "month": month,
        "label": month_label(year, month),
        "value": month_value(year, month),
        "start": start,
        "end": end,
        "has_data": has_data,
        "status": status,
        "milk_liters": milk_liters,
        "milk_revenue": milk_revenue,
        "other_income": other_income,
        "total_income": total_income,
        "total_expense": total_expense,
        "net": net,
        "net_abs": abs(net),
        "margin_pct": margin_pct,
        "margin_abs": abs(margin_pct) if margin_pct is not None else None,
        "avg_daily_liters": avg_daily_liters,
        "days_with_milk": days_with_milk,
        "revenue_per_liter": revenue_per_liter,
        "cost_per_liter": cost_per_liter,
        "break_even_rate": break_even_rate,
        "expense_rows": expense_rows,
        "income_rows": income_rows,
        "daily": daily,
        "top_animals": top_animals,
    }


def month_series(user, year, month, n=6):
    """Income / expense / profit for the n months ending at (year, month), oldest first."""
    start_year, start_month = shift_month(year, month, -(n - 1))
    start = dt.date(start_year, start_month, 1)
    end = month_bounds(year, month)[1]

    def grouped(model, value):
        rows = (
            model.objects.filter(owner=user, date__range=(start, end))
            .annotate(bucket=TruncMonth("date"))
            .values("bucket")
            .annotate(bucket_total=Sum(value))
            .order_by("bucket")
        )
        return {(r["bucket"].year, r["bucket"].month): _d(r["bucket_total"]) for r in rows}

    liters = grouped(MilkRecord, "liters")
    milk_revenue = grouped(MilkRecord, MILK_REVENUE)
    other_income = grouped(Income, "amount")
    expense = grouped(Expense, "amount")

    series = []
    for i in range(n):
        y, m = shift_month(start_year, start_month, i)
        key = (y, m)
        income_total = milk_revenue.get(key, ZERO) + other_income.get(key, ZERO)
        spent = expense.get(key, ZERO)
        series.append(
            {
                "year": y,
                "month": m,
                "value": month_value(y, m),
                "label": dt.date(y, m, 1).strftime("%b %Y"),
                "liters": liters.get(key, ZERO).quantize(CENT),
                "milk_revenue": milk_revenue.get(key, ZERO).quantize(CENT),
                "other_income": other_income.get(key, ZERO).quantize(CENT),
                "income": income_total.quantize(CENT),
                "expense": spent.quantize(CENT),
                "net": (income_total - spent).quantize(CENT),
            }
        )
    return series


def insights(summary, currency, previous_net=None):
    """Plain-language observations generated from the numbers."""
    fm = lambda v: format_money(currency, v)  # noqa: E731
    s = summary
    if not s["has_data"]:
        return ["No records for this month yet. Add milk, expense and income entries, then generate the report again."]

    tips = []
    if s["status"] == "profit":
        tips.append(f"Good month: income exceeded expenses and you made a net profit of {fm(s['net'])}.")
    elif s["status"] == "loss":
        tips.append(f"This month ran at a loss of {fm(abs(s['net']))}: expenses were higher than income.")
    else:
        tips.append("You broke even this month: income equals expenses.")

    if s["expense_rows"]:
        top = s["expense_rows"][0]
        tips.append(f"Your biggest cost was {top['label']} at {fm(top['total'])} ({top['pct']}% of all expenses).")
        feed = next((r for r in s["expense_rows"] if r["key"] == "feed"), None)
        if feed and feed["pct"] >= 60:
            tips.append(
                "Feed is more than 60% of your expenses. Compare feed prices, buy in bulk, "
                "or grow some fodder yourself to bring this down."
            )

    if s["milk_liters"] and s["cost_per_liter"] is not None:
        if s["status"] == "loss" and s["break_even_rate"] is not None:
            tips.append(
                f"To break even you would need to sell milk for about {fm(s['break_even_rate'])} per liter "
                f"(you averaged {fm(s['revenue_per_liter'])})."
            )
        elif s["status"] == "profit":
            tips.append(
                f"Each liter cost you about {fm(s['cost_per_liter'])} and earned {fm(s['revenue_per_liter'])} in milk sales."
            )
    elif s["total_expense"] and not s["milk_liters"]:
        tips.append("You have expenses but no milk records this month. Add your daily milk to get an accurate result.")

    if previous_net is not None:
        diff = s["net"] - previous_net
        if diff > 0:
            tips.append(f"Compared with last month, your result improved by {fm(diff)}.")
        elif diff < 0:
            tips.append(f"Compared with last month, your result dropped by {fm(abs(diff))}.")

    if s["top_animals"]:
        best = s["top_animals"][0]
        label = f"{best['tag']} {best['name']}".strip()
        tips.append(f"Top milk producer: {label} with {best['liters']} liters.")
    return tips
