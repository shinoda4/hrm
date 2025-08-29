import os
import uuid

from django.contrib.auth.models import AbstractUser, Permission
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def user_photo_upload_to(instance, filename):
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join("user/photos",
                        instance.date_joined.strftime("%Y/%m/%d"),
                        new_filename)


class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="邮箱")
    photo = models.ImageField(
        verbose_name="照片",
        upload_to=user_photo_upload_to,
        default="user/photos/default.png"
    )
    phone = models.CharField(verbose_name="手机", max_length=11, unique=True, blank=False, null=False)
    first_name = models.CharField("名", max_length=150, blank=True)
    last_name = models.CharField("姓", max_length=150, blank=True)
    is_staff = models.BooleanField(
        "是否为员工",
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        "是否激活",
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField("加入时间", default=timezone.now)

    def save(self, *args, **kwargs):
        self.is_active = True
        self.is_staff = True
        if not self.password:
            self.set_password("123456")
        print("saving user", self.username)

        super().save(*args, **kwargs)

        self.user_permissions.add(Permission.objects.get(codename="view_user"))
        self.user_permissions.add(Permission.objects.get(codename="add_fieldchangeapplication"))
        self.user_permissions.add(Permission.objects.get(codename="view_fieldchangeapplication"))
        self.user_permissions.add(Permission.objects.get(codename="view_applicationmessage"))

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = verbose_name
        permissions = [
            ("reset_password", "可以重置用户密码为123456"),
            ("make_superuser", "可以更改用户为超级管理员"),
        ]
