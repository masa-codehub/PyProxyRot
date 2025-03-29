# Python + Selenium プロキシ経由スクリーンショット取得ツール

## 1. プロジェクト概要

このプロジェクトは、Python と Selenium (Microsoft Edge) を使用し、ファイルから読み込んだプロキシサーバーリストを経由して、指定されたウェブサイト（デフォルトはIPアドレス確認サイト）にアクセスし、各プロキシごとのブラウザ画面をスクリーンショットとして保存するツールです。

Docker Compose を利用して、Pythonアプリケーション、Selenium WebDriver (Edge)、テスト用プロキシ (mitmproxy) を含んだ実行環境を構築・実行します。

主な目的は、Selenium の `EdgeOptions` を介してプロキシを設定する基本的な使い方を示し、複数のプロキシでの接続結果を視覚的に確認することです。TDD、DDD、クリーンアーキテクチャの原則を意識して開発されました。

## 2. 前提条件

* **Docker:** [インストール手順](https://docs.docker.com/get-docker/)
* **Docker Compose:** (Docker Desktop には通常含まれています) [インストール手順](https://docs.docker.com/compose/install/)

## 3. セットアップ手順

1.  **リポジトリのクローン (任意):**
    ```bash
    git clone <リポジトリのURL>
    cd <リポジトリ名>
    ```

2.  **`.env` ファイルの作成:**
    プロジェクトルート（`docker-compose.yml` と同じ場所）に `.env` ファイルを作成し、環境変数を設定します。以下は例です。`docker-compose.yml` 内の `${...}` 変数に合わせて調整してください。
    *(リポジトリに `.env.example` ファイルがあれば、それをコピーして編集するのがおすすめです。)*
    ```dotenv
    # .env ファイルの例
    PROJECT_NAME=PyProxyRot
    CONTAINER_VOLUME=/app

    # Selenium Hub / VNC ポート (docker-compose.yml のデフォルト値と同じなら定義不要)
    # HUB_PORT=4444
    # BROWSER_PORT=7900

    # ボリュームパス (docker-compose.yml のデフォルト値と同じなら定義不要)
    # SELENIUM_SHARED=/dev/shm
    # SELENIUM_DOWNLOADS=/app/downloads
    # LOCAL_DOWNLOADS=./downloads

    # プロキシ (mitmproxy) の Web UI パスワード (docker-compose.yml で設定したもの)
    PROXY_PASSWORD=mysecret

    # Supervisor 認証情報 (selenium コンテナの Dockerfile による)
    # SUPERVISOR_USERNAME=user
    # SUPERVISOR_PASSWORD=pass

    # アプリケーションのデフォルト設定 (任意)
    # LOG_LEVEL=DEBUG
    # APP_LOGGER_NAME=my_app_log
    # SELENIUM_HUB=http://selenium:4444/wd/hub
    ```

3.  **`proxies.txt` ファイルの作成:**
    プロジェクトルートに `proxies.txt` という名前（または `main.py` 実行時に `-f` オプションで指定する名前）のファイルを作成し、使用するプロキシリストを記述します。
    * **書式:** 1行に1プロキシを `ホスト名:ポート番号` または `ホスト名,ポート番号` で記述。
    * `#` で始まる行と空行は無視されます。
    * **★重要ルール★:** **1行目には必ず `proxy-server:8080`** (docker-compose で起動するローカルプロキシのサービス名とポート) を記述してください。これは内部的な初期化に使用され、スクリーンショットはスキップされます。実際にテストしたい外部プロキシは2行目以降に記述します。

    ```
    # proxies.txt の例
    # 1行目は docker-compose のプロキシサービスを指定
    proxy-server:8080

    # --- ここからが実際にスクショを撮るプロキシ ---
    113.160.132.195:8080
    203.99.240.179:80
    # public-proxy.com:3128
    # another.proxy,8888
    # ...
    ```

4.  **`screenshots` ディレクトリの作成:**
    プロジェクトルートにスクリーンショット保存用のディレクトリを作成します。
    ```bash
    mkdir screenshots
    ```

5.  **Docker イメージのビルドと初回起動 (証明書生成のため):**
    `selenium` イメージに `mitmproxy` の証明書を組み込むため、以下の手順で実行します。
    ```bash
    # 手順1: proxy-server を起動して証明書を生成させる (.edge/.mitmproxy/ 以下に)
    docker compose up -d --no-deps --force-recreate proxy-server
    # (少し待って証明書ファイル mitmproxy-ca-cert.pem が生成されたか確認)
    docker compose stop proxy-server # 確認後、停止してもOK

    # 手順2: selenium イメージをビルド (証明書コピーを含む)
    docker compose build selenium

    # 手順3: py-proxy-rotator イメージをビルド
    docker compose build py-proxy-rotator

    # 手順4: 全体を起動 (任意)
    # docker compose up -d
    ```
    `docker compose build selenium` でエラーが出ないことを確認してください。

## 4. アプリケーションの実行

1.  Docker Compose で全サービスを起動します（バックグラウンド実行の例）。
    ```bash
    docker compose up -d
    ```
    `docker compose ps` で全コンテナ (`py-proxy-rotator`, `selenium`, `proxy-server`) が `Up` 状態であることを確認します。

2.  `main.py` を実行してスクリーンショットを取得します。
    ```bash
    # デフォルトの proxies.txt を使用する場合
    docker compose run --rm py-proxy-rotator python main.py

    # 別のプロキシファイルを指定する場合
    # docker compose run --rm py-proxy-rotator python main.py -f my_proxies.txt

    # ログレベルを DEBUG に変更する場合
    # docker compose run --rm py-proxy-rotator python main.py -l DEBUG

    # 確認するURLを変更する場合
    # docker compose run --rm py-proxy-rotator python main.py -u [http://httpbin.org/ip](http://httpbin.org/ip)
    ```

### 出力について

* **コンソール:** 実行中のログが表示され、最後に処理結果のサマリー（成功/失敗数）が表示されます。
* **ログファイル:** コンテナ内の `/app/app.log` (デフォルト) にログが記録されます。`docker-compose.yml` でホストの `./logs` ディレクトリにマウント設定をしていれば、`./logs/app.log` で確認できます。
* **スクリーンショット:** 処理が成功したプロキシ（リストの2番目以降）について、ホストの `./screenshots` ディレクトリ内に `ip_check_proxy_インデックス_ホスト_ポート.png` という名前で画像ファイルが保存されます。

## 5. `ProxiedEdgeBrowser` クラスの基本的な使い方

このプロジェクトの中心となる `ProxiedEdgeBrowser` クラスは、以下のように Python スクリプトから利用できます。

```python
# 使い方サンプル

from src.domain.proxy_info import ProxyInfo
from src.application.proxy_provider import ListProxyProvider
from src.application.proxy_selector import ProxySelector
from src.adapters.edge_option_factory import EdgeOptionFactory
from src.application.proxied_edge_browser import ProxiedEdgeBrowser
from src.config.logging_config import setup_logging

# 0. ロギング設定 (任意)
setup_logging()

# 1. 依存関係の準備
# プロキシリストは ListProxyProvider 経由で渡す
proxy_list = [
    ProxyInfo(host="proxy-server", port=8080), # 最初のプロキシ (必須)
    ProxyInfo(host="[external.proxy.com](https://www.google.com/search?q=external.proxy.com)", port=3128)
]
provider = ListProxyProvider(proxy_list)
selector = ProxySelector(provider)
factory = EdgeOptionFactory() # --ignore-certificate-errors を含む実装
selenium_hub_url = "http://selenium:4444/wd/hub" # Docker Compose環境の場合

# 2. ProxiedEdgeBrowser のインスタンス化 (with文推奨)
try:
    with ProxiedEdgeBrowser(selector, factory, selenium_hub_url) as browser:
        # 3. ブラウザを起動 (リストのインデックスを指定)
        # 最初のプロキシ (index=0) は初期化用、スクショはスキップされる想定
        browser.start_browser(proxy_index=0)
        print("最初のプロキシでブラウザ起動完了 (スクショなし)")
        # 最初のブラウザは with を抜けるときに閉じられる

    # 2番目のプロキシで再度実行
    with ProxiedEdgeBrowser(selector, factory, selenium_hub_url) as browser:
        browser.start_browser(proxy_index=1)

        # 4. 操作 (例: スクリーンショット)
        target_url = "[https://ipinfo.io/what-is-my-ip](https://ipinfo.io/what-is-my-ip)"
        save_path = "/app/screenshots/example_screenshot.png" # コンテナ内パス
        browser.take_screenshot(target_url, save_path)
        print(f"プロキシ #1 でスクリーンショットを {save_path} に保存しました。")

except Exception as e:
    print(f"エラーが発生しました: {e}")

# 'with' ブロックを抜けると自動的に browser.close_browser() が呼ばれる
```

## 6. テストの実行

ユニットテストと結合テストが用意されています。

* **ユニットテスト:** 個々のコンポーネントをテストします。
    ```bash
    docker compose run --rm py-proxy-rotator python -m pytest tests
    ```
* **結合テスト:** Docker Compose 環境全体を起動してテストします。
    ```bash
    # まずコンテナを起動
    docker compose up -d

    # integration マークが付いたテストを実行
    docker compose run --rm py-proxy-rotator python -m pytest -m integration tests/integration
    ```

## 7. プロジェクト構成 (主要部分)

```
.
├── .env                   # 環境変数定義ファイル (要作成)
├── Dockerfile             # (py-proxy-rotator 用 - .build 内かも)
├── docker-compose.yml     # Docker Compose 定義ファイル
├── main.py                # アプリケーション実行スクリプト
├── proxies.txt            # プロキシリストファイル (要作成)
├── pyproject.toml         # プロジェクト設定・依存関係 (Poetryなど)
├── README.md              # このファイル
├── screenshots/           # スクリーンショット保存先 (要作成)
├── src/                   # ソースコード
│   ├── adapters/
│   ├── application/
│   ├── config/
│   └── domain/
└── tests/                 # テストコード
    ├── application/
    ├── adapters/
    ├── config/
    ├── domain/
    ├── integration/
    └── conftest.py
```
(注: `Dockerfile` や `pyproject.toml` の場所はプロジェクト構成によります)

## 8. 既知の問題点・回避策

* **HTTPS証明書エラー回避:** 現在の実装では、プロキシ経由でのHTTPSアクセス時の証明書エラーを回避するため、Edgeの起動オプションに `--ignore-certificate-errors` を追加しています。これはテスト目的の措置であり、セキュリティリスクが伴います。
* **最初のプロキシのスキップ:** 初回起動時にプロキシ設定が有効にならない現象への回避策として、`proxies.txt` の1行目には必ず `proxy-server:8080` を記述し、そのプロキシでのスクリーンショット取得はスキップする運用としています。
