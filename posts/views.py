from django.shortcuts import render, redirect, get_object_or_404
from .forms import PostForm
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from .models import Like, Post # 1. Comment のインポートを削除
from django.db.models import Count
import json
from django.db.models import Count, Case, When, BooleanField

def index(request):
    posts = (
            Post.objects.select_related('author', 'quoted_post', 'quoted_post__author')
            .filter(commented_post__isnull=True)
            .annotate(
                like_count_anno=Count('likes', distinct=True),
                comment_count_anno=Count('comments', distinct=True),
                quote_count_anno=Count('quoted_post__quoted_by', distinct=True)
            )
            .order_by("-post_id")
        )
                        
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
            new_comment_count = original_post.comments.count()
            
            # ★★★ 修正点: ユーザーアイコンURLの取得ロジックを安全に変更 ★★★
            # ユーザーアイコンがある場合はそのURLを返し、ない場合は空の文字列を返す
            icon_url = new_comment.author.icon.url if new_comment.author.icon else ""
            
            return JsonResponse({
                "ok": True,
                "post_id": new_comment.post_id,
                # ユーザー情報 (authorから取得)
                "username": new_comment.author.username,
                "display_name": new_comment.author.display_name,
                "icon_url": icon_url, # 修正した変数を使用
                # コメント本文
                "content": new_comment.content,
                "original_author_username": original_author_username,
                "comment_count": new_comment_count
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

# posts/views.py (delete_post 関数) の修正

@login_required
def delete_post(request, post_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"})

    post_to_delete = get_object_or_404(Post, post_id=post_id)

    # 投稿者のみ削除可能
    if request.user != post_to_delete.author:
        return JsonResponse({"error": "Permission denied"})
        
    # ★ コメントだった場合、親投稿のIDを取得しておく ★
    original_post_id = post_to_delete.commented_post.post_id if post_to_delete.commented_post else None

    post_to_delete.delete()
    
    # ★ 削除されたのがコメントだった場合、コメント数を再計算して返す ★
    new_comment_count = None
    if original_post_id:
        try:
            original_post = Post.objects.get(post_id=original_post_id)
            new_comment_count = original_post.comments.count()
        except Post.DoesNotExist:
            pass # 元の投稿が既に削除されていた場合は無視

    return JsonResponse({
        "ok": True,
        "new_comment_count": new_comment_count # コメント数を含めて返す
    })

def post_detail(request, post_id): 
    # 4. 関数が重複定義されていたため、統合されたロジックを使用
    current_user = request.user
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

    comments = Post.objects.select_related('author') \
                           .filter(commented_post__post_id=post_id) \
                           .annotate(
                               # コメントにユーザーがいいねしているかの判定 (is_liked_anno) を追加
                               is_liked_anno=Case(
                                   When(likes__user=current_user, then=True),
                                   default=False,
                                   output_field=BooleanField()
                               ),
                               like_count_anno=Count('likes', distinct=True),
                               quote_count_anno=Count('quoted_post__quoted_by', distinct=True),
                               comment_count_anno=Count('comments', distinct=True),
                           ) \
                           .order_by("post_id")
    
    comment_list = []
    for comment in comments:
        comment_list.append({
            'post_id': comment.post_id,
            'content': comment.content,
            'author': comment.author,
            'created_at': comment.created_at,
            'image': comment.image,
            # ★★★ ここで is_liked の値を設定 ★★★
            'is_liked': comment.is_liked_anno,
            'like_count': comment.like_count_anno,
            'quote_count': comment.quote_count_anno,
            'comment_count': comment.comment_count_anno,
            # commented_post はコメント元の投稿なので不要
        })
    
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
        'comments': comment_list,
    }
    return render(request, 'posts/detail.html', context)