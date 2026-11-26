from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.monthly, name="monthly"),
    path("export/csv/", views.export_csv, name="csv"),
    path("export/pdf/", views.export_pdf, name="pdf"),
    path("yearly/", views.yearly, name="yearly"),
]
