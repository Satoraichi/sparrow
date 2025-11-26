from django.shortcuts import redirect
from django.urls import reverse

class LoginRequiredMiddleware:
    """
    ログインしていない場合はログインページへリダイレクトする
    例外: ログインページ、ログアウト、静的ファイルなど
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # ログインしていない場合
        if not request.user.is_authenticated:
            login_url = reverse("accounts:login")
            # 許可するパスのリスト
            allowed_paths = [
                login_url,
                reverse("accounts:logout"),
                "/admin/",
                "/static/",
                "/media/",
            ]
            if not any(request.path.startswith(path) for path in allowed_paths):
                return redirect(f"{login_url}?next={request.path}")

        response = self.get_response(request)
        return response
