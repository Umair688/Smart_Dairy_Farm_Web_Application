from animals.models import Animal
from core.forms import DateInput, FarmModelForm

from .models import Expense


class ExpenseForm(FarmModelForm):
    class Meta:
        model = Expense
        fields = ["date", "category", "amount", "description", "animal"]
        widgets = {"date": DateInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["animal"].queryset = Animal.objects.filter(owner=self.user)
        self.fields["animal"].empty_label = "Not linked to an animal"
