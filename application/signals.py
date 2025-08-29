# application/signals.py
from django.contrib.auth.models import Permission
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def rename_default_permissions(sender, **kwargs):
    perms = Permission.objects.filter(
        codename__in=[
            'add_fieldchangeapplication',
            'change_fieldchangeapplication',
            'delete_fieldchangeapplication',
            'view_fieldchangeapplication',
            'add_applicationmessage',
            'change_applicationmessage',
            'delete_applicationmessage',
            'view_applicationmessage',
        ]
    )
    mapping = {
        'add_fieldchangeapplication': '添加个人信息更改申请',
        'change_fieldchangeapplication': '修改个人信息更改申请',
        'delete_fieldchangeapplication': '删除个人信息更改申请',
        'view_fieldchangeapplication': '查看个人信息更改申请',
        'add_applicationmessage': '添加申请信息',
        'change_applicationmessage': '修改申请信息',
        'delete_applicationmessage': '删除申请信息',
        'view_applicationmessage': '查看申请信息',
    }
    for perm in perms:
        perm.name = mapping.get(perm.codename, perm.name)
        perm.save()
