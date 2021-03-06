from typing import Set

from django.contrib.auth.models import Permission
from django.db import models
from oauthlib.common import generate_token

from ..core.models import ModelWithMetadata
from ..core.permissions import AppPermission


class App(ModelWithMetadata):
    name = models.CharField(max_length=60)
    created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        help_text="Specific permissions for this app.",
        related_name="app_set",
        related_query_name="app",
    )

    class Meta:
        ordering = ("name", "pk")
        permissions = ((AppPermission.MANAGE_APPS.codename, "Manage apps",),)

    def _get_permissions(self) -> Set[str]:
        """Return the permissions of the app."""
        if not self.is_active:
            return set()
        perm_cache_name = "_app_perm_cache"
        if not hasattr(self, perm_cache_name):
            perms = self.permissions.all()
            perms = perms.values_list("content_type__app_label", "codename").order_by()
            setattr(self, perm_cache_name, {f"{ct}.{name}" for ct, name in perms})
        return getattr(self, perm_cache_name)

    def has_perms(self, perm_list):
        """Return True if the app has each of the specified permissions."""
        if not self.is_active:
            return False

        wanted_perms = {perm.value for perm in perm_list}
        actual_perms = self._get_permissions()

        return (wanted_perms & actual_perms) == wanted_perms

    def has_perm(self, perm):
        """Return True if the app has the specified permission."""
        if not self.is_active:
            return False

        return perm.value in self._get_permissions()


class AppToken(models.Model):
    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name="tokens")
    name = models.CharField(blank=True, default="", max_length=128)
    auth_token = models.CharField(default=generate_token, unique=True, max_length=30)
