from core.mixins import FarmCreateView, FarmDeleteView, FarmListView, FarmUpdateView

from .forms import AnimalForm
from .models import Animal


class AnimalListView(FarmListView):
    model = Animal
    title = "Animals"
    columns = (
        ("Tag", "tag_number", ""),
        ("Name", "name", ""),
        ("Type", "animal_type", ""),
        ("Breed", "breed", ""),
        ("Status", "status", ""),
        ("Age", "age_display", ""),
        ("Purchase price", "purchase_price", "money"),
    )
    search_fields = ("tag_number", "name", "breed")
    choice_field = "status"
    choice_label = "Status"

    def get_totals(self, qs):
        return [
            ("Animals shown", qs.count()),
            ("Lactating", qs.filter(status="lactating").count()),
        ]


class AnimalCreateView(FarmCreateView):
    model = Animal
    form_class = AnimalForm


class AnimalUpdateView(FarmUpdateView):
    model = Animal
    form_class = AnimalForm


class AnimalDeleteView(FarmDeleteView):
    model = Animal
