from django.shortcuts import render, redirect, get_object_or_404
from .forms import PostForm
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from .models import Like, Post
from django.db.models import Count, Case, When, BooleanField
import json
from django.db.models import Q # Qをインポート

# =========================================================
# 補助関数：祖先投稿の再帰的な取得
# =========================================================
def get_post_ancestors(post):
    """
    現在のPostオブジェクトから最上位の親投稿まで、すべての祖先投稿を取得する。
    """
    ancestors = []
    current_post = post
    
    # commented_post が null になるまで遡る (ただし、元のPostオブジェクトを直接参照する)
    while current_post.commented_post:
        # 祖先をリストに追加 (古いコメントがリストの先頭になる)
        ancestors.insert(0, current_post.commented_post)
        
        # 次の親投稿へ移動
        current_post = current_post.commented_post
        
    return ancestors

# =========================================================
# index
# =========================================================
def index(request):
    # (既存の index 関数ロジック...省略)
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
                        
    if request.method == "POST":
        if request.user.is_authenticated:
            if "toggle_like" in request.POST:
                post_id = request.POST.get("post_id")
                post = get_object_or_404(Post, post_id=post_id) 
                like, created = Like.objects.get_or_create(post=post, user=request.user)
                if not created:
                    like.delete()
                return redirect("posts:index")

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

    for post in posts:
        if request.user.is_authenticated:
            post.is_liked = post.likes.filter(user=request.user).exists()
        else:
            post.is_liked = False
            
        post.like_count = post.like_count_anno
        post.comment_count = post.comment_count_anno
        post.quote_count = post.quote_count_anno

    context = {
        "posts": posts,
        "form": form,
        "current_user": request.user,
    }
    return render(request, "posts/index.html", context)

# =========================================================
# toggle_like, add_comment, quote_post, delete_post, timeline (省略)
# =========================================================

@login_required
def toggle_like(request):
    if request.method == "POST":
        post_id = request.POST.get("post_id")
        post = get_object_or_404(Post, post_id=post_id)
        like, created = Like.objects.get_or_create(post=post, user=request.user)
        if not created:
            like.delete()

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
            new_comment = Post.objects.create(
                author=request.user,
                content=content,
                commented_post=original_post
            )

            original_author_username = original_post.author.username
            new_comment_count = original_post.comments.count()
            
            icon_url = new_comment.author.icon.url if new_comment.author.icon else ""
            
            return JsonResponse({
                "ok": True,
                "post_id": new_comment.post_id,
                "username": new_comment.author.username,
                "display_name": new_comment.author.display_name,
                "icon_url": icon_url,
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

@login_required
def delete_post(request, post_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"})

    post_to_delete = get_object_or_404(Post, post_id=post_id)

    if request.user != post_to_delete.author:
        return JsonResponse({"error": "Permission denied"})
        
    original_post_id = post_to_delete.commented_post.post_id if post_to_delete.commented_post else None

    post_to_delete.delete()
    
    new_comment_count = None
    if original_post_id:
        try:
            original_post = Post.objects.get(post_id=original_post_id)
            new_comment_count = original_post.comments.count()
        except Post.DoesNotExist:
            pass

    return JsonResponse({
        "ok": True,
        "new_comment_count": new_comment_count
    })


# =========================================================
# post_detail (祖先取得ロジックを組み込み)
# =========================================================
@login_required
def post_detail(request, post_id): 
    current_user = request.user
    
    # 1. メイン投稿の生のオブジェクトを取得
    main_post_raw = get_object_or_404(
        Post.objects.select_related('author', 'quoted_post', 'quoted_post__author')
                    .prefetch_related('comments', 'comments__author'),
        post_id=post_id
    )

    # 2. 祖先投稿の生のオブジェクトリストを取得 (再帰)
    ancestor_posts_raw = get_post_ancestors(main_post_raw)
    
    # 3. メイン投稿とすべての祖先投稿のIDリストを作成
    post_ids_to_fetch = [p.post_id for p in ancestor_posts_raw] + [main_post_raw.post_id]
    
    # 4. すべての関連投稿を一度にアノテーション付きで取得し直す
    annotated_posts = Post.objects.select_related('author', 'quoted_post', 'quoted_post__author') \
                                  .filter(post_id__in=post_ids_to_fetch) \
                                  .annotate(
                                      is_liked_anno=Case(
                                          When(likes__user=current_user, then=True), default=False, output_field=BooleanField()
                                      ),
                                      like_count_anno=Count('likes', distinct=True),
                                      comment_count_anno=Count('comments', distinct=True),
                                      quote_count_anno=Count('quoted_post__quoted_by', distinct=True),
                                  )

    # 5. 取得したデータをIDでマップ
    annotated_map = {p.post_id: p for p in annotated_posts}
    
    # 6. ラッピング関数
    def wrap_post_data(p):
        return {
            'post_id': p.post_id,
            'content': p.content,
            'author': p.author,
            'author_username': p.author.username,
            'created_at': p.created_at,
            'image': p.image,
            'quoted_post': p.quoted_post,
            'repost': p.repost,
            # アノテーション結果をフィールドとして追加
            'is_liked': getattr(p, 'is_liked_anno', False),
            'like_count': getattr(p, 'like_count_anno', 0),
            'quote_count': getattr(p, 'quote_count_anno', 0),
            'comment_count': getattr(p, 'comment_count_anno', 0),
            'is_comment': p.commented_post is not None, # コメントかどうかのフラグ
        }

    # 7. メイン投稿と祖先投稿のデータを整備
    annotated_main_post = annotated_map.get(main_post_raw.post_id)
    annotated_ancestors = [annotated_map.get(p.post_id) for p in ancestor_posts_raw]

    # 8. コメントの取得 (メイン投稿に紐づく直下のコメントのみ)
    comments_queryset = Post.objects.select_related('author') \
                                  .filter(commented_post=annotated_main_post) \
                                  .annotate(
                                      is_liked_anno=Case(When(likes__user=current_user, then=True), default=False, output_field=BooleanField()),
                                      like_count_anno=Count('likes', distinct=True),
                                      quote_count_anno=Count('quoted_post__quoted_by', distinct=True),
                                      comment_count_anno=Count('comments', distinct=True),
                                  ) \
                                  .order_by("post_id") 

    comment_list = [wrap_post_data(comment) for comment in comments_queryset]
    
    context = {
        'current_user': current_user,
        'post': wrap_post_data(annotated_main_post), # メイン投稿
        'ancestor_posts_path': [wrap_post_data(p) for p in annotated_ancestors if p], # 祖先投稿のリスト
        'comments': comment_list, # 直下のコメント
    }
    return render(request, 'posts/detail.html', context)