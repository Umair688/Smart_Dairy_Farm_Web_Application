from core.forms import DateInput, FarmModelForm

from .models import Income


class IncomeForm(FarmModelForm):
    class Meta:
        model = Income
        fields = ["date", "source", "amount", "description"]
        widgets = {"date": DateInput()}
