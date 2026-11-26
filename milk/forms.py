from django import forms

from accounts.models import get_profile
from animals.models import Animal
from core.forms import DateInput, FarmModelForm

from .models import MilkRecord


class MilkRecordForm(FarmModelForm):
    class Meta:
        model = MilkRecord
        fields = ["date", "session", "animal", "liters", "rate_per_liter", "fat_percent", "notes"]
        widgets = {"date": DateInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["animal"].queryset = Animal.objects.filter(owner=self.user)
        self.fields["animal"].empty_label = "Whole herd (no specific animal)"
        if not self.instance.pk:
            self.fields["rate_per_liter"].initial = get_profile(self.user).default_milk_rate
