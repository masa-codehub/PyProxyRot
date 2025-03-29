# Python + Selenium プロキシ経由スクリーンショット取得ツール

## 概要

このプロジェクトは、Python と Selenium (Microsoft Edge) を使用し、指定されたプロキシサーバーリストを経由して特定のウェブサイトにアクセスし、その結果をスクリーンショットとして保存するサンプルアプリケーションです。Docker Compose を使用して、アプリケーション実行環境、Selenium Standalone Edge 環境、およびテスト用プロキシ (mitmproxy) を構築・実行します。

主な目的は、Selenium の `EdgeOptions` を介してプロキシを設定し、各プロキシ経由での接続結果（IPアドレス確認サイトの表示）を視覚的に確認する基本的な仕組みを提供することです。

## 機能

* プロキシリストをファイル (`proxies.txt` など) から読み込み
* リスト内の各プロキシを順番に使用してブラウザを起動
* 指定されたURL (デフォルトは IP 確認サイト) にアクセス
* 各プロキシ使用時のブラウザ画面をスクリーンショットとして保存
* Docker Compose による環境構築 (Pythonアプリ, Selenium Edge, mitmproxy)
* 基本的なエラーハンドリング（特定のプロキシ失敗時に処理を続行）
* ロギング機能 (ファイルおよびコンソール)

## 要件

* Docker
* Docker Compose

## セットアップ手順

1.  **リポジトリのクローン (もし Git 管理している場合):**
    ```bash
    git clone <リポジトリのURL>
    cd <リポジトリ名>
    ```

2.  **`.env` ファイルの作成:**
    プロジェクトルートに `.env` ファイルを作成し、Docker Compose で使用する環境変数を定義します。最低限、以下の変数が必要になる可能性があります (`docker-compose.yml` の `${...}` 部分に合わせてください)。
    ```dotenv
    # .env ファイルの例
    PROJECT_NAME=PyProxyRot
    CONTAINER_VOLUME=/app
    SELENIUM_HUB=http://selenium:4444/wd/hub
    HUB_PORT=4444
    BROWSER_PORT=7900 # VNCを使わないなら不要な場合あり
    SELENIUM_SHARED=/dev/shm # または適切な共有パス
    SELENIUM_DOWNLOADS=/app/downloads # 例: コンテナ内のダウンロードパス
    LOCAL_DOWNLOADS=./downloads       # 例: ホスト側のダウンロードパス
    PROXY_PASSWORD=mysecret          # mitmproxy の Web UI 用パスワード (任意)
    # SUPERVISOR_USERNAME=user       # seleniumコンテナのSupervisor用 (Dockerfileによる)
    # SUPERVISOR_PASSWORD=pass       # seleniumコンテナのSupervisor用 (Dockerfileによる)
    # LOG_LEVEL=DEBUG                # ログレベル (任意)
    # APP_LOGGER_NAME=my_app_log     # ロガー名 (任意)
    ```
    ※ `docker-compose.yml` でデフォルト値 (`:-...`) が設定されている変数は、`.env` で定義しなくても動作します。

3.  **`proxies.txt` ファイルの作成:**
    プロジェクトルートに `proxies.txt` という名前のファイルを作成し、使用したいプロキシサーバーのリストを記述します。**注意点として、現在の実装では以下の規約が必要です。**
    * **1行目:** 必ず Docker Compose で起動するローカルプロキシ (`proxy-server:8080` など) を記述してください。これは内部的な初期化/ウォームアップに使用され、スクリーンショットはスキップされます。
    * **2行目以降:** IPアドレスを確認したい外部プロキシなどを `ホスト名:ポート番号` または `ホスト名,ポート番号` の形式で記述します。
    * `#` で始まる行と空行は無視されます。

    ```
    # proxies.txt の例
    # 1行目は docker-compose のプロキシサービスを指定
    proxy-server:8080

    # --- ここから実際に確認したいプロキシ ---
    113.160.132.195:8080
    203.99.240.179:80
    # [public-proxy.com:3128](https://www.google.com/search?q=public-proxy.com:3128)
    # another.proxy,8888
    # ...
    ```

4.  **`screenshots` ディレクトリの作成:**
    プロジェクトルートに、スクリーンショットを保存するためのディレクトリを作成します。
    ```bash
    mkdir screenshots
    ```
    （もし `docker-compose.yml` の `volumes` 設定で `./screenshots` 以外を指定した場合は、そのディレクトリを作成してください。）

5.  **Docker イメージのビルド:**
    `mitmproxy` の証明書を `selenium` イメージにコピーする必要があるため、段階的にビルド・起動します。
    ```bash
    # 1. proxy-server を起動して証明書を生成させる
    docker compose up -d --no-deps --force-recreate proxy-server
    # (少し待って ./PyProxyRot/.edge/.mitmproxy/mitmproxy-ca-cert.pem ができるか確認)
    # docker compose stop proxy-server # 停止してもOK

    # 2. selenium イメージをビルド (証明書コピーを含む)
    docker compose build selenium

    # 3. 必要であれば py-proxy-rotator もビルド
    docker compose build py-proxy-rotator
    ```

## アプリケーションの実行

1.  Docker Compose で全サービスを起動します（バックグラウンド実行の例）。
    ```bash
    docker compose up -d
    ```
    `docker compose ps` で全コンテナ (`py-proxy-rotator`, `selenium`, `proxy-server`) が `Up` 状態であることを確認します。

2.  `main.py` を実行します。
    * **デフォルト (`proxies.txt`, `https://ipinfo.io/what-is-my-ip`) で実行:**
        ```bash
        docker compose run --rm py-proxy-rotator python main.py
        ```
    * **プロキシファイルを指定して実行:**
        ```bash
        # 例: my_proxies.txt を使う場合 (ファイルがマウントされている必要あり)
        docker compose run --rm py-proxy-rotator python main.py -f my_proxies.csv
        ```
    * **ログレベルやターゲットURLを変更する場合:**
        ```bash
        docker compose run --rm py-proxy-rotator python main.py -f proxies.txt -l DEBUG -u [http://httpbin.org/ip](http://httpbin.org/ip)
        ```

3.  **結果の確認:**
    * コンソールに処理のログが表示されます。
    * 実行完了後、ホストマシンの `./screenshots` ディレクトリ内に、プロキシごとに `ip_check_proxy_インデックス_ホスト_ポート.png` という名前でスクリーンショットが保存されます（プロキシ#0 を除く）。
    * 各画像を開き、表示されているIPアドレスを確認してください。
    * `mitmproxy` の Web UI (`http://localhost:8081`) で通信の詳細を確認できます（パスワードは `.env` または `docker-compose.yml` で設定したもの）。

## テストの実行

1.  **ユニットテスト:**
    コンテナを起動せずに（あるいは起動したままでも）実行できます。
    ```bash
    # アプリケーションの全ユニットテストを実行
    docker compose run --rm py-proxy-rotator python -m pytest tests/application tests/adapters tests/config tests/domain
    # または単に
    # docker compose run --rm py-proxy-rotator python -m pytest tests
    ```

2.  **結合テスト:**
    Docker Compose 環境 (`py-proxy-rotator`, `selenium`, `proxy-server`) が**起動している必要**があります。
    ```bash
    # まずコンテナを起動
    docker compose up -d

    # integration マークが付いたテストを実行
    docker compose run --rm py-proxy-rotator python -m pytest -m integration tests/integration
    ```

## プロジェクト構成 (主要部分)

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
│   ├── adapters/          # アダプター層 (EdgeOptionFactoryなど)
│   ├── application/       # アプリケーション層 (ProxiedEdgeBrowser, ProxySelectorなど)
│   ├── config/            # 設定関連 (logging_configなど)
│   └── domain/            # ドメイン層 (ProxyInfoなど)
└── tests/                 # テストコード
    ├── application/
    ├── adapters/
    ├── config/
    ├── domain/
    └── integration/       # 結合テスト
    └── conftest.py        # pytest フィクスチャ定義
```
(注: `Dockerfile` や `requirements.txt` / `pyproject.toml` の場所は、あなたの `docker-compose.yml` の `build.context` 設定によります)

## 既知の問題点・回避策

* **HTTPS証明書エラー:** プロキシ (`mitmproxy`) 経由でHTTPSサイトにアクセスする際、ブラウザで証明書エラーが発生します。現在の実装では、これを回避するために Selenium の `EdgeOptions` で `--ignore-certificate-errors` を指定しています。これはテスト目的の回避策であり、セキュリティリスクを伴います。根本解決には Selenium コンテナへの `mitmproxy` CA証明書の適切なインストールが必要です（Dockerfileでの手順は試みましたが、EdgeブラウザがOSストアを認識しない可能性があり、完全には解決していません）。
* **最初のプロキシの挙動:** リストの最初のプロキシを使用した場合に、指定したプロキシ設定が有効にならない現象が確認されました。回避策として、`proxies.txt` の1行目には必ず動作確認済みのローカルプロキシ (`proxy-server:8080`) を記述し、そのプロキシでのスクリーンショット処理はスキップするようにしています。
