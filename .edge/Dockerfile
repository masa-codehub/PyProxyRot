# 1. ベースイメージを選択:
FROM selenium/standalone-edge:126.0

# FROM selenium/standalone-edge:latest
# FROM selenium/standalone-chrome:latest

# 2. 作業ディレクトリを設定:
WORKDIR ${SELENIUM_SHARED}

# 3. 環境変数を設定:    
ENV PYTHONIOENCODING=utf-8
ENV TZ="Asia/Tokyo"
ENV LANG=ja_JP.UTF-8
ENV LANGUAGE=ja_JP:ja

# root 権限で実行
USER root

# 証明書ファイルをコンテナ内の適切な場所にコピー
# COPY 元のパスをビルドコンテキストからの相対パスに修正
COPY ./.mitmproxy/mitmproxy-ca-cert.pem /usr/local/share/ca-certificates/mitmproxy-ca-cert.crt

# OSの証明書ストアを更新
RUN apt-get update && apt-get install -y ca-certificates && update-ca-certificates && rm -rf /var/lib/apt/lists/*
#   ↑ update-ca-certificates を実行するために ca-certificates パッケージが必要な場合があるため追記

# --- 証明書インストール処理ここまで ---

# 元のユーザーに戻す (もし USER 命令があれば)
USER seluser 
