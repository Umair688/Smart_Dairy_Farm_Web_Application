from django import forms

from core.forms import DateInput, FarmModelForm

from .models import Animal


class AnimalForm(FarmModelForm):
    class Meta:
        model = Animal
        fields = [
            "tag_number", "name", "animal_type", "breed", "date_of_birth",
            "status", "purchase_price", "notes",
        ]
        widgets = {
            "date_of_birth": DateInput(),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_tag_number(self):
        tag = self.cleaned_data["tag_number"].strip()
        duplicates = Animal.objects.filter(owner=self.user, tag_number__iexact=tag)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError("You already have an animal with this tag number.")
        return tag
