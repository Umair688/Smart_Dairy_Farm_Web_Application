from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from core.models import OwnedModel
from core.utils import today


class Income(OwnedModel):
    """Income other than daily milk sales (milk revenue is counted automatically)."""

    SOURCE_CHOICES = [
        ("animal_sale", "Animal sale"),
        ("calf_sale", "Calf sale"),
        ("manure", "Manure / dung sale"),
        ("subsidy", "Subsidy / grant"),
        ("other", "Other"),
    ]

    date = models.DateField(default=today)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="other")
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-date", "-id"]
        verbose_name = "income"
        verbose_name_plural = "income"

    def __str__(self):
        return f"{self.date} {self.get_source_display()} - {self.amount}"
