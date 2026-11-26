from django.contrib import admin

from .models import MilkRecord


@admin.register(MilkRecord)
class MilkRecordAdmin(admin.ModelAdmin):
    list_display = ("date", "session", "animal", "liters", "rate_per_liter", "owner")
    list_filter = ("session", "date")
