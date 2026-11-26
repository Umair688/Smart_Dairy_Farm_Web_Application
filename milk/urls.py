from django.urls import path

from . import views

app_name = "milk"

urlpatterns = [
    path("", views.MilkListView.as_view(), name="list"),
    path("add/", views.MilkCreateView.as_view(), name="add"),
    path("<int:pk>/edit/", views.MilkUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.MilkDeleteView.as_view(), name="delete"),
]
