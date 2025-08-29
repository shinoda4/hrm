from django.contrib import admin, messages
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from import_export.admin import ImportExportModelAdmin

from user.models import User


# Register your models here.
@admin.register(User)
class UserAdmin(ImportExportModelAdmin):
    list_display = ['username', 'email', 'is_superuser', 'is_staff', 'is_active']
    search_fields = ['username', 'email']
    actions = ['make_superuser', 'reset_password']
    exclude = ['password']

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = ["date_joined", "last_login"]
        if request.user.is_superuser:
            return readonly_fields
        else:
            # 返回新的列表
            return readonly_fields + ["username", "user_permissions", "groups", "is_superuser", "is_staff", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_obj = None

    def save_model(self, request, obj, form, change):
        if change:  # 只有修改时才取旧值
            self._old_obj = obj.__class__.objects.get(pk=obj.pk)
        else:
            self._old_obj = None
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.has_perm("user.change_user"):
            return qs
        return qs.filter(id=request.user.id)

    def has_change_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser and obj.is_superuser:
            return False

        if obj is not None and not request.user.is_superuser and obj.id != request.user.id and obj.is_superuser:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return super().has_delete_permission(request, obj)

    def has_add_permission(self, request):
        return super().has_add_permission(request)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            # 非超级用户不能改这些字段
            for field in ["is_superuser", "is_staff", "is_active", "groups", "user_permissions"]:
                if field in form.base_fields:
                    form.base_fields[field].disabled = True
        return form

    @admin.action(description="标记所选用户为管理员")
    def make_superuser(self, request, queryset):
        queryset.update(is_superuser=True)

    @admin.action(description="重置密码为123456")
    def reset_password(self, request, queryset):
        for user in queryset:
            user.set_password("123456")
            user.save()
        self.message_user(request, f"{queryset.count()} 个用户的密码已重置为 123456", messages.SUCCESS)

    def log_change(self, request, obj, message):
        changes = []
        if hasattr(self, "_old_obj") and self._old_obj:
            for field in obj._meta.fields:
                if field.name in ["updated_at", "created_at"]:
                    continue
                field_name = field.name
                old_val = getattr(self._old_obj, field_name, None)
                new_val = getattr(obj, field_name, None)
                if old_val != new_val:
                    changes.append(f"{field.verbose_name}: {old_val} → {new_val}")

        if changes:
            custom_message = "已修改字段: " + "; ".join(changes)
        else:
            custom_message = "无变更"

        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(obj).pk,
            object_id=obj.pk,
            object_repr=str(obj),
            action_flag=CHANGE,
            change_message=custom_message
        )
