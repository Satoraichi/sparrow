from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    path('', views.index, name='index'),
    # いいね機能
    path("toggle_like/", views.toggle_like, name="toggle_like"),
    path('add_comment/<str:post_id>/', views.add_comment, name='add_comment'),

]
