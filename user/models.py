import os
import uuid

from django.contrib.auth.models import AbstractUser, Permission
from django.db import models


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
    salary = models.IntegerField(default=0, verbose_name="薪资(RMB)")

    def save(self, *args, **kwargs):
        self.is_active = True
        self.is_staff = True
        if not self.password:
            self.set_password("123456")
        print("saving user", self.username)

        super().save(*args, **kwargs)

        self.user_permissions.add(Permission.objects.get(codename="view_user"))

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = verbose_name
