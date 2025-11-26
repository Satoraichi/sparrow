from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # 表示名（ニックネーム）
    display_name = models.CharField(max_length=30, blank=True)

    # プロフィール画像
    icon = models.ImageField(
        upload_to='user_icons/',
        blank=True,
        null=True,
        default='user_icons/default.png'
    )

    def __str__(self):
        return self.display_name or self.username
