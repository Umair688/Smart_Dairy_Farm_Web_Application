from decimal import Decimal

from django.db import models

from core.models import OwnedModel
from core.utils import today


class Animal(OwnedModel):
    TYPE_CHOICES = [
        ("cow", "Cow"),
        ("buffalo", "Buffalo"),
        ("goat", "Goat"),
        ("calf", "Calf"),
        ("bull", "Bull"),
        ("other", "Other"),
    ]
    STATUS_CHOICES = [
        ("lactating", "Lactating"),
        ("dry", "Dry"),
        ("pregnant", "Pregnant"),
        ("heifer", "Heifer / Calf"),
        ("sold", "Sold"),
        ("dead", "Dead"),
    ]
    INACTIVE_STATUSES = ("sold", "dead")

    tag_number = models.CharField("Tag number", max_length=30)
    name = models.CharField(max_length=60, blank=True)
    animal_type = models.CharField("Type", max_length=10, choices=TYPE_CHOICES, default="cow")
    breed = models.CharField(max_length=60, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="lactating")
    purchase_price = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"),
        help_text="Leave 0 if born on the farm.",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["tag_number"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "tag_number"], name="unique_tag_per_owner")
        ]

    def __str__(self):
        return f"{self.tag_number} {self.name}".strip()

    @property
    def is_active(self):
        return self.status not in self.INACTIVE_STATUSES

    @property
    def age_display(self):
        if not self.date_of_birth:
            return ""
        t = today()
        months = (t.year - self.date_of_birth.year) * 12 + (t.month - self.date_of_birth.month)
        if t.day < self.date_of_birth.day:
            months -= 1
        months = max(months, 0)
        years, rem = divmod(months, 12)
        if years:
            return f"{years}y {rem}m" if rem else f"{years}y"
        return f"{rem}m"
