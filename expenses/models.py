from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from animals.models import Animal
from core.models import OwnedModel
from core.utils import today


class Expense(OwnedModel):
    CATEGORY_CHOICES = [
        ("feed", "Feed & fodder"),
        ("medicine", "Medicine"),
        ("vet", "Veterinary / vaccination"),
        ("labour", "Labour / salaries"),
        ("electricity", "Electricity & water"),
        ("equipment", "Equipment & repairs"),
        ("transport", "Transport"),
        ("animal_purchase", "Animal purchase"),
        ("other", "Other"),
    ]

    date = models.DateField(default=today)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="feed")
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    description = models.CharField(max_length=200, blank=True)
    animal = models.ForeignKey(
        Animal, null=True, blank=True, on_delete=models.SET_NULL, related_name="expenses",
        help_text="Optional - link the cost to one animal (e.g. a vet visit).",
    )

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.date} {self.get_category_display()} - {self.amount}"

    @property
    def animal_display(self):
        return str(self.animal) if self.animal_id else ""
