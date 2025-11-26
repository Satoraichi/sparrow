# forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm

class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': 'ユーザー名を入力',
                'class': 'form-input',       # 任意のクラスを付与
                'autocomplete': 'username',  # ブラウザ補完
            }
        ),
        label=''  # ラベルを非表示にする場合
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'パスワードを入力',
                'class': 'form-input',
                'autocomplete': 'current-password',
            }
        ),
        label=''
    )
