from django.shortcuts import render, redirect
from .forms import PostForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import Http404
from .models import Comment, Like, Post
from django.db.models import Count
from django.http import JsonResponse
import json

def index(request):
    # [2] クエリセットの取得とアノテーション（集計）
    posts = Post.objects.select_related('author', 'quoted_post', 'quoted_post__author') \
                        .annotate(
                            like_count_anno=Count('likes', distinct=True),      # いいね数を集計
                            comment_count_anno=Count('comments', distinct=True), # コメント数を集計
                            quote_count_anno=Count('quoted_by', distinct=True)    # 引用数(リポスト数)を集計
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
    # ループ内で count() を呼び出す代わりに、アノテーション結果を使用する
    for post in posts:
        # 個人のいいね判定 (個別のクエリが必要)
        if request.user.is_authenticated:
            post.is_liked = post.likes.filter(user=request.user).exists()
        else:
            post.is_liked = False
            
        # アノテーションの結果をテンプレート変数に割り当てる
        # これにより、テンプレート側で post.like_count などとしてアクセス可能になる
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

def add_comment(request, post_id):
    if request.method == "POST" and request.user.is_authenticated:
        post = get_object_or_404(Post, post_id=post_id)
        text = request.POST.get("text", "").strip()
        if text:
            comment = Comment.objects.create(post=post, user=request.user, text=text)
            return JsonResponse({
                "comment_id": comment.comment_id,
                "username": comment.user.username,
                "display_name": comment.user.display_name,
                "icon_url": comment.user.icon.url if comment.user.icon else "",
                "text": comment.text,
                "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })
    return JsonResponse({"error": "Invalid request"}, status=400)

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

from django.shortcuts import render, get_object_or_404
from django.http import Http404
# from .models import Post (Postモデルがインポートされている必要があります)

def post_detail(request, post_id): # post_id は str 型として渡される

    # 1. 文字列を BigInt として扱うために整数に変換
    try:
        post_id_int = int(post_id) 
    except ValueError:
        # IDが数字ではない（例: "abc"）場合は404
        raise Http404("Invalid post ID format.")

    # 2. データベース検索 (変換した整数値を使用)
    # 検索キーは必ず 'pk=post_id_int' と、変換後の整数を使用する
    post = get_object_or_404(
        Post.objects.select_related('author', 'quoted_post', 'quoted_post__author')
                    .prefetch_related('comments', 'comments__user'), 
        post_id=post_id  # ★ ここを post_id= に変更する！
    )
    
    # その投稿に紐づくコメントも取得
    comments = post.comments.all().order_by('created_at')

    # 詳細表示用のテンプレートにデータを渡す
    context = {
        'post': post,
        'comments': comments,
        'current_user': request.user,
    }
    
    # 3. テンプレートのレンダリング
    return render(request, 'posts/detail.html', context)

def post_detail(request, post_id): 
    try:
        # URLから受け取った文字列を整数に変換
        post_id_int = int(post_id) 
    except ValueError:
        raise Http404("Invalid post ID format.")

    # データベース検索と集計 (annotate) を同時に実行
    post = get_object_or_404(
        Post.objects.select_related('author', 'quoted_post', 'quoted_post__author')
                    .prefetch_related('comments', 'comments__user')
                    .annotate(
                        like_count_anno=Count('likes', distinct=True),
                        comment_count_anno=Count('comments', distinct=True),
                        quote_count_anno=Count('quoted_by', distinct=True) # 引用（リポスト）数をカウント
                    ), 
        post_id=post_id # post_id (CharField) で検索
    )
    
    # テンプレートでアクセスしやすいように、集計結果を属性として割り当てる (オプション)
    post.like_count = post.like_count_anno
    post.comment_count = post.comment_count_anno
    post.quote_count = post.quote_count_anno

    # 個人のいいね判定
    if request.user.is_authenticated:
        post.is_liked = post.likes.filter(user=request.user).exists()
    else:
        post.is_liked = False
    
    comments = post.comments.all().order_by('created_at')

    context = {
        'post': post,
        'comments': comments,
        'current_user': request.user,
    }
    return render(request, 'posts/detail.html', context)