from django.contrib import admin
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType

from .models import FieldChangeApplication, ApplicationMessage


class ApplicationMessageInline(admin.StackedInline):
    model = ApplicationMessage
    extra = 0
    readonly_fields = ["application", "user", "content", "created_at"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # 普通用户只能看自己的消息
        if not request.user.is_superuser:
            return qs.filter(user=request.user)
        # 如果你希望超级用户也有限制，比如只能看“自己审批过的消息”
        # return qs.filter(approval_user=request.user)
        return qs

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(FieldChangeApplication)
class FieldChangeApplicationAdmin(admin.ModelAdmin):
    list_display = ["user", "field_name", "new_value", "status", "updated_at"]
    list_filter = ["status"]
    search_fields = ["user__username", "field_name"]
    inlines = [ApplicationMessageInline]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_obj = None

    def get_exclude(self, request, obj=None):
        if not request.user.is_superuser:
            return ["user", "old_value", "archived"]  # 非超级用户隐藏 old_value
        return ()  # 超级用户不隐藏

    actions = ["approve_application", "reject_application"]

    def has_change_permission(self, request, obj=None):
        qs = self.get_queryset(request)
        if obj:
            return qs.filter(archived=False).exists()
        return False

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            # 非超级用户不能改这些字段
            for field in ["status"]:
                if field in form.base_fields:
                    form.base_fields[field].disabled = True
        return form

    def save_model(self, request, obj, form, change):
        if change:  # 只有修改时才取旧值
            self._old_obj = obj.__class__.objects.get(pk=obj.pk)
        else:
            self._old_obj = None
        if not change or not obj.user_id:
            obj.user = request.user
        if obj.status == "pending":
            obj.pending_application(request)
        if obj.status == "approved":
            obj.approve_application(request)
        if obj.status == "rejected":
            if request.user == obj.user:
                obj.pending_application(request)
            else:
                obj.reject_application(request)
        super().save_model(request, obj, form, change)

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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def approve_application(self, request, queryset):
        for app in queryset:
            if app.status != "approved":
                app.approve_application(request)

    approve_application.short_description = "批准所选申请"

    def reject_application(self, request, queryset):
        for app in queryset:
            if app.status != "rejected":
                app.reject_application(request)

    reject_application.short_description = "驳回所选申请"
