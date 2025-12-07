from django.db import models

from django.db import models
from django.conf import settings
from django.utils import timezone
from ckeditor_uploader.fields import RichTextUploadingField
import uuid

def generate_post_id():
    # ポストIDを12桁の10進数で生成
    # timestamp をベースに生成する方式（重複しにくい）
    return int(timezone.now().timestamp() * 1000)  # 13桁になるのであとで切る

class Post(models.Model):
    post_id = models.CharField(max_length=12, unique=True, editable=False)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts"
    )

    content = RichTextUploadingField(blank=True, null=True) 
    image = models.ImageField(upload_to="post_images/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    quoted_post = models.ForeignKey(
        "self",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="quoted_by"
    )

    def save(self, *args, **kwargs):
        if not self.post_id:
            # 13桁 → 12桁にトリム
            self.post_id = str(generate_post_id())[:12]
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-post_id"]  # post_id 降順（新しい投稿が上）

    repost = models.BooleanField(default=False)

class Comment(models.Model):
    comment_id = models.CharField(max_length=12, unique=True, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.comment_id:
            # 12桁のランダムなIDを生成
            self.comment_id = str(uuid.uuid4().int)[:12]
        super().save(*args, **kwargs)


class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("post", "user")  # 同じユーザーが同じ投稿に複数いいねできない

    def __str__(self):
        return f"{self.user.username} likes {self.post.post_id}"

class Bookmark(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="bookmarks")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')

class Repost(models.Model):
    original_post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reposts")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('original_post', 'user')
