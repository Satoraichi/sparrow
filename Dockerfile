# Pythonのベースイメージ
FROM python:3.10-slim

# サーバー側で静的ファイルを処理するために必要なパッケージ（PostgreSQLのクライアント含む）
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリの設定
WORKDIR /app

# 依存関係ファイルのコピーとインストール
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# プロジェクトコードのコピー
COPY . /app

# 静的ファイルの収集
RUN python manage.py collectstatic --noinput

# コンテナ起動時に実行するコマンド (Procfileと同じ内容)
CMD ["gunicorn", "sparrow.wsgi:application", "--bind", "0.0.0.0:8000"]