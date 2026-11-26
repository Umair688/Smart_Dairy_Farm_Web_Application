from django import forms


class DateInput(forms.DateInput):
    """HTML5 date picker that pre-fills correctly when editing."""

    input_type = "date"

    def __init__(self, **kwargs):
        kwargs.setdefault("format", "%Y-%m-%d")
        super().__init__(**kwargs)


class FarmModelForm(forms.ModelForm):
    """ModelForm that receives the logged-in user (used to scope dropdowns)."""

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
