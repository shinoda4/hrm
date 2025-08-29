from django.contrib import admin
from django.contrib.auth.models import Permission


class CustomPermissionAdmin(admin.ModelAdmin):
    pass


admin.site.register(Permission, CustomPermissionAdmin)
