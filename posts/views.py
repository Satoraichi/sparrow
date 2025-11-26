from django.shortcuts import render, redirect
from .forms import PostForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import Comment, Like, Post
from django.http import JsonResponse

def index(request):
    posts = Post.objects.all()

    # 新規投稿処理（元のまま）
    if request.method == "POST":
        if request.user.is_authenticated:
            # いいねボタン押下か判定
            if "toggle_like" in request.POST:
                post_id = request.POST.get("post_id")
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

    # 各投稿のいいね判定＆いいね数
    for post in posts:
        if request.user.is_authenticated:
            post.is_liked = post.likes.filter(user=request.user).exists()
        else:
            post.is_liked = False
        post.like_count = post.likes.count()

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