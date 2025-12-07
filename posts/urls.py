from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    path('', views.index, name='index'),
    # いいね機能
    path("toggle_like/", views.toggle_like, name="toggle_like"),
    path("delete/<str:post_id>/", views.delete_post, name="delete_post"),
    path('add_comment/<str:post_id>/', views.add_comment, name='add_comment'),
    path("posts/quote/", views.quote_post, name="quote_post"),
    path('posts/<str:post_id>/', views.post_detail, name='detail'),
]
