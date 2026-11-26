from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from animals.models import Animal
from core.models import OwnedModel
from core.utils import today


class MilkRecord(OwnedModel):
    SESSION_CHOICES = [("morning", "Morning"), ("evening", "Evening")]

    animal = models.ForeignKey(
        Animal, null=True, blank=True, on_delete=models.SET_NULL, related_name="milk_records",
        help_text="Leave empty to record milk for the whole herd.",
    )
    date = models.DateField(default=today)
    session = models.CharField(max_length=10, choices=SESSION_CHOICES, default="morning")
    liters = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    rate_per_liter = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0"))],
        help_text="Selling price per liter.",
    )
    fat_percent = models.DecimalField(
        "Fat %", max_digits=4, decimal_places=1, null=True, blank=True
    )
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-date", "-session", "-id"]
        verbose_name = "milk record"
        verbose_name_plural = "milk records"

    def __str__(self):
        return f"{self.date} {self.get_session_display()} - {self.liters} L"

    @property
    def amount(self):
        return (self.liters * self.rate_per_liter).quantize(Decimal("0.01"))

    @property
    def animal_display(self):
        return str(self.animal) if self.animal_id else "Whole herd"
