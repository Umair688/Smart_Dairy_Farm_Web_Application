import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from accounts.models import get_profile
from core.utils import month_value, parse_month, shift_month, today

from .pdf import build_monthly_pdf
from .services import insights, month_series, month_summary


def _f(value):
    return float(value)


def _report_context(user, year, month):
    currency = get_profile(user).currency
    summary = month_summary(user, year, month)
    series = month_series(user, year, month, 6)
    previous_net = series[-2]["net"] if len(series) > 1 and series[-2]["income"] + series[-2]["expense"] else None
    return summary, series, insights(summary, currency, previous_net), get_profile(user)


@login_required
def monthly(request):
    year, month = parse_month(request.GET.get("month"))
    summary, series, tips, profile = _report_context(request.user, year, month)
    prev_y, prev_m = shift_month(year, month, -1)
    next_y, next_m = shift_month(year, month, 1)
    chart = {
        "days": [d["day"] for d in summary["daily"]],
        "liters": [_f(d["liters"]) for d in summary["daily"]],
        "income": [_f(d["income"]) for d in summary["daily"]],
        "expense": [_f(d["expense"]) for d in summary["daily"]],
        "cat_labels": [r["label"] for r in summary["expense_rows"]],
        "cat_values": [_f(r["total"]) for r in summary["expense_rows"]],
        "trend_labels": [r["label"] for r in series],
        "trend_income": [_f(r["income"]) for r in series],
        "trend_expense": [_f(r["expense"]) for r in series],
    }
    future = (year, month) >= (today().year, today().month)
    return render(
        request,
        "reports/monthly.html",
        {
            "s": summary,
            "series": series,
            "insights": tips,
            "chart": chart,
            "month_value": summary["value"],
            "prev_value": month_value(prev_y, prev_m),
            "next_value": None if future else month_value(next_y, next_m),
            "farm": profile,
        },
    )


@login_required
def export_csv(request):
    year, month = parse_month(request.GET.get("month"))
    s = month_summary(request.user, year, month)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="dairy-report-{s["value"]}.csv"'
    w = csv.writer(response)
    w.writerow(["Monthly profit & loss report", s["label"]])
    w.writerow([])
    w.writerow(["Item", "Value"])
    w.writerow(["Milk produced (L)", s["milk_liters"]])
    w.writerow(["Milk sales", s["milk_revenue"]])
    w.writerow(["Other income", s["other_income"]])
    w.writerow(["Total income", s["total_income"]])
    w.writerow(["Total expenses", s["total_expense"]])
    w.writerow(["Net profit / loss", s["net"]])
    w.writerow(["Result", s["status"]])
    w.writerow([])
    w.writerow(["Expense category", "Amount", "Share %"])
    for r in s["expense_rows"]:
        w.writerow([r["label"], r["total"], r["pct"]])
    w.writerow([])
    w.writerow(["Income source", "Amount", "Share %"])
    for r in s["income_rows"]:
        w.writerow([r["label"], r["total"], r["pct"]])
    w.writerow([])
    w.writerow(["Day", "Milk (L)", "Income", "Expense"])
    for d in s["daily"]:
        w.writerow([d["day"], d["liters"], d["income"], d["expense"]])
    return response


@login_required
def export_pdf(request):
    year, month = parse_month(request.GET.get("month"))
    summary, _series, tips, profile = _report_context(request.user, year, month)
    try:
        pdf_bytes = build_monthly_pdf(summary, profile.farm_name, profile.currency, tips)
    except ImportError:
        messages.error(request, "PDF export needs ReportLab. Run: pip install reportlab")
        return redirect(f"{reverse('reports:monthly')}?month={summary['value']}")
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="dairy-report-{summary["value"]}.pdf"'
    return response


@login_required
def yearly(request):
    try:
        year = int(request.GET.get("year", today().year))
    except ValueError:
        year = today().year
    year = min(max(year, 1900), 2200)
    series = month_series(request.user, year, 12, 12)
    totals = {
        "liters": sum(r["liters"] for r in series),
        "income": sum(r["income"] for r in series),
        "expense": sum(r["expense"] for r in series),
        "net": sum(r["net"] for r in series),
    }
    chart = {
        "labels": [r["label"] for r in series],
        "income": [_f(r["income"]) for r in series],
        "expense": [_f(r["expense"]) for r in series],
        "net": [_f(r["net"]) for r in series],
    }
    return render(
        request,
        "reports/yearly.html",
        {
            "series": series,
            "totals": totals,
            "year": year,
            "prev_year": year - 1,
            "next_year": year + 1,
            "chart": chart,
            "profit_months": sum(1 for r in series if r["net"] > 0),
            "loss_months": sum(1 for r in series if r["net"] < 0),
        },
    )
