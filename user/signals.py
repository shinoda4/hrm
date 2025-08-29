from django.contrib.auth.models import Permission
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def rename_default_permissions(sender, **kwargs):
    perms = Permission.objects.filter(
        codename__in=[
            'add_user',
            'change_user',
            'delete_user',
            'view_user',
        ]
    )
    mapping = {
        'add_user': '添加用户',
        'change_user': '修改用户信息',
        'delete_user': '删除用户',
        'view_user': '查看用户信息',
    }
    for perm in perms:
        perm.name = mapping.get(perm.codename, perm.name)
        perm.save()
