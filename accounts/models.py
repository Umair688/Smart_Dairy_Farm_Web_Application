from decimal import Decimal

from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    farm_name = models.CharField(max_length=120, default="My Dairy Farm")
    phone = models.CharField(max_length=30, blank=True)
    currency = models.CharField(
        "Currency label",
        max_length=8,
        default="Rs",
        help_text="Shown before amounts, e.g. Rs, PKR, USD. Use plain letters so PDF reports print correctly.",
    )
    default_milk_rate = models.DecimalField(
        "Default milk rate per liter",
        max_digits=8,
        decimal_places=2,
        default=Decimal("100.00"),
        help_text="Pre-filled when you add a milk record. You can change it on each record.",
    )

    def __str__(self):
        return f"{self.farm_name} ({self.user})"


def get_profile(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile
