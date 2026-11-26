from django.conf import settings
from django.db import models


class OwnedModel(models.Model):
    """Base class: every farm record belongs to exactly one user.

    All views filter on ``owner`` so each user only ever sees their own farm.
    """

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
