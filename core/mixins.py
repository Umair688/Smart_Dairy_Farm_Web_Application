"""Generic, owner-scoped CRUD views shared by animals, milk, expenses, income."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from accounts.models import get_profile

from .utils import format_money, month_bounds, parse_month


class OwnedQuerysetMixin(LoginRequiredMixin):
    """Only ever expose rows that belong to the logged-in user."""

    def get_queryset(self):
        return super().get_queryset().filter(owner=self.request.user)


class FarmListView(OwnedQuerysetMixin, ListView):
    paginate_by = 20
    template_name = "core/list.html"
    title = ""
    columns = ()  # tuples of (header, attribute, kind) - kind: "", money, liters, date
    search_fields = ()
    date_field = None  # enables the month filter
    choice_field = None  # enables a dropdown filter on a field with choices
    choice_label = ""
    select_related = ()

    def get_queryset(self):
        qs = super().get_queryset()
        if self.select_related:
            qs = qs.select_related(*self.select_related)

        query = self.request.GET.get("q", "").strip()
        if query and self.search_fields:
            condition = Q()
            for field in self.search_fields:
                condition |= Q(**{f"{field}__icontains": query})
            qs = qs.filter(condition)

        month = self.request.GET.get("month")
        if self.date_field and month:
            start, end = month_bounds(*parse_month(month))
            qs = qs.filter(**{f"{self.date_field}__range": (start, end)})

        choice = self.request.GET.get("choice")
        if self.choice_field and choice:
            qs = qs.filter(**{self.choice_field: choice})
        return qs

    def money(self, value):
        return format_money(get_profile(self.request.user).currency, value)

    def get_totals(self, qs):
        return []

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        meta = self.model._meta
        params = self.request.GET.copy()
        params.pop("page", None)
        choices = []
        if self.choice_field:
            choices = list(meta.get_field(self.choice_field).choices)
        ctx.update(
            title=self.title or meta.verbose_name_plural.title(),
            singular=meta.verbose_name.title(),
            ns=meta.app_label,
            columns=self.columns,
            q=self.request.GET.get("q", ""),
            month=self.request.GET.get("month", ""),
            has_month=bool(self.date_field),
            has_search=bool(self.search_fields),
            choice_options=choices,
            choice_label=self.choice_label,
            choice_value=self.request.GET.get("choice", ""),
            querystring=params.urlencode(),
            totals=self.get_totals(self.object_list),
        )
        return ctx


class FarmFormMixin(OwnedQuerysetMixin):
    template_name = "core/form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse(f"{self.model._meta.app_label}:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        name = self.model._meta.verbose_name.title()
        ctx["title"] = f"Edit {name}" if getattr(self, "object", None) else f"Add {name}"
        ctx["cancel_url"] = self.get_success_url()
        return ctx

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f"{self.model._meta.verbose_name.title()} saved.")
        return response


class FarmCreateView(FarmFormMixin, CreateView):
    pass


class FarmUpdateView(FarmFormMixin, UpdateView):
    pass


class FarmDeleteView(OwnedQuerysetMixin, DeleteView):
    template_name = "core/confirm_delete.html"

    def get_success_url(self):
        return reverse(f"{self.model._meta.app_label}:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = self.get_success_url()
        ctx["singular"] = self.model._meta.verbose_name.title()
        return ctx

    def form_valid(self, form):
        messages.success(
            self.request, f"{self.model._meta.verbose_name.title()} deleted."
        )
        return super().form_valid(form)
