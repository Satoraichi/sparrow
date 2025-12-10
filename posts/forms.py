# posts/forms.py
from django import forms
from .models import Post

class PostForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'rows': 1,
                'placeholder': '今なにしてる？',
                'class': 'autoresize',
                'style': 'overflow:hidden; resize:none;'
            }
        ),
        label=''
    )

    class Meta:
        model = Post
        fields = ['content', 'image']

class CommentForm(forms.ModelForm):
    text = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'rows': 1,
                'placeholder': 'コメントする…',
                'class': 'autoresize_new',  # JSで自動リサイズ
                'style': 'overflow:hidden; resize:none;'
            }
        ),
        label=''
    )