from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from .forms import ProfileForm, RegisterForm
from .models import get_profile


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("dashboard:home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(
            self.request, "Welcome! Your farm account is ready. Start by adding your animals."
        )
        return response


class ProfileView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    template_name = "core/form.html"
    success_url = reverse_lazy("accounts:profile")
    extra_context = {"title": "Farm profile", "cancel_url": reverse_lazy("dashboard:home")}

    def get_object(self, queryset=None):
        return get_profile(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Farm profile updated.")
        return super().form_valid(form)


class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = "core/form.html"
    success_url = reverse_lazy("accounts:profile")
    extra_context = {"title": "Change password", "cancel_url": reverse_lazy("accounts:profile")}

    def form_valid(self, form):
        messages.success(self.request, "Password changed.")
        return super().form_valid(form)
