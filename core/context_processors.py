def farm(request):
    """Expose the farm name and currency symbol to every template."""
    if request.user.is_authenticated:
        from accounts.models import get_profile

        profile = get_profile(request.user)
        return {"farm_name": profile.farm_name, "currency": profile.currency}
    return {"farm_name": "Smart Dairy Farm", "currency": "Rs"}
