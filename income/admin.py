from django.contrib import admin

from .models import Income


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ("date", "source", "amount", "owner")
    list_filter = ("source", "date")
