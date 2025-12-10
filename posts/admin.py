from django.contrib import admin

from django.contrib import admin
from .models import Post, Comment, Like, Bookmark, Repost

# Post 管理画面
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('post_id', 'author', 'created_at', 'content_summary')
    search_fields = ('content', 'author__username')
    ordering = ('-created_at',)

    def content_summary(self, obj):
        return obj.content[:50]
    content_summary.short_description = 'Content'

# コメント・いいね・ブックマーク・リポストも登録（閲覧用）
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'user', 'created_at')
    search_fields = ('post__content', 'user__username')

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'user', 'created_at')
    search_fields = ('post__content', 'user__username')

@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'user', 'created_at')
    search_fields = ('post__content', 'user__username')

@admin.register(Repost)
class RepostAdmin(admin.ModelAdmin):
    list_display = ('id', 'original_post', 'user', 'created_at', 'comment_summary')
    search_fields = ('original_post__content', 'user__username', 'comment')

    def comment_summary(self, obj):
        return obj.comment[:50]  # 最初の50文字
    comment_summary.short_description = 'Comment'

