from django.urls import path

from . import views

app_name = "income"

urlpatterns = [
    path("", views.IncomeListView.as_view(), name="list"),
    path("add/", views.IncomeCreateView.as_view(), name="add"),
    path("<int:pk>/edit/", views.IncomeUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.IncomeDeleteView.as_view(), name="delete"),
]
