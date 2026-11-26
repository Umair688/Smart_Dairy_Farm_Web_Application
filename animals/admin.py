from django.contrib import admin

from .models import Animal


@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ("tag_number", "name", "animal_type", "status", "owner")
    list_filter = ("status", "animal_type")
    search_fields = ("tag_number", "name")
