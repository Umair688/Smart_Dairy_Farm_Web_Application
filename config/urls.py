from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("animals/", include("animals.urls")),
    path("milk/", include("milk.urls")),
    path("expenses/", include("expenses.urls")),
    path("income/", include("income.urls")),
    path("reports/", include("reports.urls")),
    path("", include("dashboard.urls")),
]
