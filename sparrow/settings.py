"""
Django settings for sparrow project.
"""

from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# 1. SECURITY & DEBUGGING
# ==============================================================================

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-k30irhcktxj3&dfjn9@%*z_f%g_in^$rr@23pc1u9!&dzec5qi')

# 環境変数で DEBUG モードを制御
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

# ALLOWED_HOSTS の設定
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# 本番環境ホストの追加 (Vercel/Renderなど)
# Vercel/Render のホスト名
EXTERNAL_HOST = os.environ.get('RENDER_EXTERNAL_HOSTNAME') or os.environ.get('VERCEL_URL')
if EXTERNAL_HOST:
    ALLOWED_HOSTS.append(EXTERNAL_HOST)

# 開発環境でのすべてのホストを許可 (0.0.0.0対応)
if DEBUG:
    ALLOWED_HOSTS.append('*')


# ==============================================================================
# 2. APPLICATION DEFINITION
# ==============================================================================

INSTALLED_APPS = [
    # Django Core Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-Party Apps
    'ckeditor',
    'ckeditor_uploader',
    'sslserver',           # HTTPSローカル開発用
    'django_extensions',   # runserver_plus用
    
    # Local Apps
    'posts',
    'accounts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # 静的ファイル対応（本番用）
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "accounts.middleware.LoginRequiredMiddleware",
]

ROOT_URLCONF = 'sparrow.urls'

# ... (TEMPLATES, WSGI_APPLICATION の設定は省略) ...


# ==============================================================================
# 3. DATABASE
# ==============================================================================

# 環境変数 'DATABASE_URL' があれば本番DB、なければローカルSQLiteを使用
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(default=DATABASE_URL)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# ==============================================================================
# 4. I18N & AUTH
# ==============================================================================

LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_TZ = True

AUTH_USER_MODEL = 'accounts.User'
LOGIN_URL = '/accounts/login/' # ログインが必要なページのURL


# ==============================================================================
# 5. STATIC & MEDIA FILES
# ==============================================================================

# 静的ファイルの URL パス (共通)
STATIC_URL = 'static/'

# 開発環境で探すディレクトリ (runserver用)
STATICFILES_DIRS = [
    BASE_DIR / "static"
]

# 本番デプロイ時にファイルを収集する場所 (collectstatic用)
STATIC_ROOT = BASE_DIR / "staticfiles" 

# メディアファイル (ユーザーアップロード)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "mediafiles" # メディアファイルの保存場所

CKEDITOR_UPLOAD_PATH = "uploads/"


# ==============================================================================
# 6. LOCAL DEVELOPMENT SETTINGS
# ==============================================================================

# runserver_plus が 0.0.0.0:8000 で起動するように設定
RUNSERVERPLUS_SERVER_ADDRESS_PORT = '0.0.0.0:8000'

# HTTPS リダイレクト設定 (開発中は False)
SECURE_SSL_REDIRECT = False