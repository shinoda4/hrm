from django.db import models

from user.models import User


class FieldChangeApplication(models.Model):
    STATUS_CHOICES = [
        ("pending", "待审批"),
        ("approved", "已批准"),
        ("rejected", "已驳回"),
    ]
    FIELD_CHOICES = [
        # ("salary", "薪资(RMB)"),
        ("username", "用户名"),
    ]
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="applications", verbose_name="用户"
    )
    field_name = models.CharField(
        max_length=50, choices=FIELD_CHOICES, verbose_name="字段"
    )
    old_value = models.TextField(verbose_name="旧值")
    new_value = models.TextField(verbose_name="新值")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="状态"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    archived = models.BooleanField(default=False, verbose_name="已归档")

    def save(self, *args, **kwargs):
        if not self.pk:  # 对象还没保存过，即首次创建
            self.old_value = getattr(self.user, self.field_name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "个人信息更改申请"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user} 提交修改 {self.field_name}"

    def pending_application(self, request):
        request_user = self.user
        setattr(request_user, self.field_name, self.new_value)
        request_user.save()

        content = f"等待审批 {self.field_name}: {self.old_value} -> {self.new_value}"
        ApplicationMessage.objects.create(application=self, user=request_user, content=content,
                                          approval_user=request.user)

        self.status = "pending"
        self.archived = False
        self.save()

    def approve_application(self, request):
        request_user = self.user
        setattr(request_user, self.field_name, self.new_value)
        request_user.save()

        content = f"批准申请 {self.field_name}: {self.old_value} -> {self.new_value}"
        ApplicationMessage.objects.create(application=self, user=request_user, content=content,
                                          approval_user=request.user)

        self.status = "approved"
        self.archived = True
        self.save()

    def reject_application(self, request):
        request_user = self.user
        print("驳回申请")
        content = f"驳回申请 {self.field_name}: {self.old_value} -> {self.new_value}"
        ApplicationMessage.objects.create(application=self, user=request_user, content=content,
                                          approval_user=request.user)

        self.status = "rejected"
        self.save()


class ApplicationMessage(models.Model):
    application = models.ForeignKey(
        FieldChangeApplication,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="申请"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="提交用户"
    )
    content = models.TextField(verbose_name="内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    approval_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="approval_user",
        verbose_name="审批用户"
    )

    def __str__(self):
        return f"{self.user}: {self.content}"

    class Meta:
        verbose_name = "申请变更历史信息"
        verbose_name_plural = verbose_name
