from django.shortcuts import render, redirect, get_object_or_404
from .forms import PostForm
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from .models import Like, Post # 1. Comment のインポートを削除
from django.db.models import Count
import json

def index(request):
    # [2] クエリセットの取得とアノテーション（集計）
    posts = Post.objects.select_related('author', 'quoted_post', 'quoted_post__author') \
                        .annotate(
                            like_count_anno=Count('likes', distinct=True),      # いいね数を集計
                            comment_count_anno=Count('comments', distinct=True), # コメント数を集計
                            quote_count_anno=Count('quoted_post__quoted_by', distinct=True) # 引用数(リポスト数)を集計
                        ) \
                        .order_by("-post_id")
                        
    # 新規投稿処理（元のまま）
    if request.method == "POST":
        if request.user.is_authenticated:
            # いいねボタン押下か判定
            if "toggle_like" in request.POST:
                post_id = request.POST.get("post_id")
                # Post ID (CharField)で検索
                post = get_object_or_404(Post, post_id=post_id) 
                like, created = Like.objects.get_or_create(post=post, user=request.user)
                if not created:
                    like.delete()  # 既にいいね済みなら解除
                return redirect("posts:index")

            # 投稿フォーム処理
            form = PostForm(request.POST, request.FILES)
            if form.is_valid():
                post = form.save(commit=False)
                post.author = request.user
                post.save()
                return redirect("posts:index")
        else:
            return redirect("login")
    else:
        form = PostForm()

    # [3] 各投稿のいいね判定と、集計結果の割り当て
    for post in posts:
        # 個人のいいね判定 (個別のクエリが必要)
        if request.user.is_authenticated:
            post.is_liked = post.likes.filter(user=request.user).exists()
        else:
            post.is_liked = False
            
        # アノテーションの結果をテンプレート変数に割り当てる
        post.like_count = post.like_count_anno
        post.comment_count = post.comment_count_anno
        post.quote_count = post.quote_count_anno

    context = {
        "posts": posts,
        "form": form,
        "current_user": request.user,
    }
    return render(request, "posts/index.html", context)

@login_required
def toggle_like(request):
    if request.method == "POST":
        post_id = request.POST.get("post_id")
        post = get_object_or_404(Post, post_id=post_id)
        like, created = Like.objects.get_or_create(post=post, user=request.user)
        if not created:
            like.delete()  # 既にいいね済みなら解除

        # 現在のいいね数と状態を返す
        return JsonResponse({
            "is_liked": post.likes.filter(user=request.user).exists(),
            "like_count": post.likes.count()
        })
    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
def add_comment(request, post_id):
    if request.method == 'POST':
        original_post = get_object_or_404(Post, post_id=post_id)
        content = request.POST.get('text')
        
        if content:
            # Postモデルとしてコメントを作成
            new_comment = Post.objects.create(
                author=request.user,
                content=content,
                commented_post=original_post
            )

            original_author_username = original_post.author.username
            
            # ★★★ 修正点: 新しいコメントの情報をJSONで返す ★★★
            return JsonResponse({
                "ok": True,
                "post_id": new_comment.post_id,
                # ユーザー情報 (authorから取得)
                "username": new_comment.author.username,
                "display_name": new_comment.author.display_name,
                "icon_url": new_comment.author.icon.url if new_comment.author.icon else None,
                # コメント本文
                "content": new_comment.content,
                # 投稿時間 (JS側で timesince を処理しない場合はこちらで文字列化)
                # "created_at": new_comment.created_at.strftime("%Y-%m-%d %H:%M:%S")
                "original_author_username": original_author_username
            })
    
    return JsonResponse({"error": "Invalid request or content missing"}, status=400)

@login_required
def quote_post(request):
    data = json.loads(request.body)
    text = data.get("text")
    quoted_post_id = data.get("quoted_post_id")

    quoted_post = get_object_or_404(Post, post_id=quoted_post_id)

    new_post = Post.objects.create(
        author=request.user,
        content=text,
        quoted_post=quoted_post,
        repost=True
    )

    return JsonResponse({"ok": True, "new_post_id": new_post.post_id})

def timeline(request):
    posts = Post.objects.select_related("quoted_post").order_by("-created_at")
    return render(request, "timeline.html", {"posts": posts})

def delete_post(request, post_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"})

    post = get_object_or_404(Post, post_id=post_id)

    # 投稿者のみ削除可能
    if request.user != post.author:
        return JsonResponse({"error": "Permission denied"})

    post.delete()
    return JsonResponse({"ok": True})

def post_detail(request, post_id): 
    # 4. 関数が重複定義されていたため、統合されたロジックを使用

    # データベース検索と集計 (annotate) を同時に実行
    post = get_object_or_404(
        Post.objects.select_related('author', 'quoted_post', 'quoted_post__author')
                    # コメントは Post モデルのインスタンスとして related_name='comments' で取得
                    .prefetch_related('comments', 'comments__author') 
                    .annotate(
                        like_count_anno=Count('likes', distinct=True),
                        comment_count_anno=Count('comments', distinct=True),
                        quote_count_anno=Count('quoted_post__quoted_by', distinct=True) # 引用数をカウント
                    ), 
        post_id=post_id # post_id (CharField) で検索
    )
    
    # テンプレートでアクセスしやすいように、集計結果を属性として割り当てる
    post.like_count = post.like_count_anno
    post.comment_count = post.comment_count_anno
    post.quote_count = post.quote_count_anno

    # 個人のいいね判定
    if request.user.is_authenticated:
        post.is_liked = post.likes.filter(user=request.user).exists()
    else:
        post.is_liked = False
    
    # 4. コメントの取得：Post モデルのインスタンスとして取得する
    comments = post.comments.all().select_related('author').order_by('created_at')

    context = {
        'post': post,
        'comments': comments,
        'current_user': request.user,
    }
    return render(request, 'posts/detail.html', context)