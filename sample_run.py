# sample_run.py

import os
import sys
import logging
from time import sleep

# --- 必要なクラス/関数を src からインポート ---
# (src ディレクトリが Python のパスに含まれている必要があります)
try:
    from src.domain.proxy_info import ProxyInfo
    from src.application.proxy_provider import ListProxyProvider
    from src.application.proxy_selector import ProxySelector
    from src.adapters.edge_option_factory import EdgeOptionFactory
    from src.application.proxied_edge_browser import ProxiedEdgeBrowser
    from src.config.logging_config import setup_logging, get_logger
except ImportError as e:
    print(f"ERROR: Could not import necessary modules from src: {e}")
    print("Make sure PYTHONPATH is set correctly or run from the project root.")
    sys.exit(1)

# --- 設定 ---
# Selenium Hub のURL (環境変数またはデフォルト)
SELENIUM_URL = os.getenv('SELENIUM_HUB', 'http://selenium:4444/wd/hub')

# スクリーンショットを撮る対象のURL
TARGET_IP_CHECK_URL = "https://ipinfo.io/what-is-my-ip"
# TARGET_IP_CHECK_URL = "https://api.ipify.org?format=json" # こちらでも可

# コンテナ内のスクリーンショット保存先ディレクトリ
# (docker-compose.yml でホストの ./screenshots にマウントされている想定)
SCREENSHOT_DIR_CONTAINER = "/app/screenshots"

# --- テスト用プロキシリスト ---
# 実際のプロキシ情報や、テスト用のダミー情報を記述
# docker-compose で起動している mitmproxy を含める
proxy_definitions = [
    {"host": "proxy-server", "port": 8080},  # docker-compose のサービス名
    # {"host": "192.168.1.100", "port": 3128}, # 例: 別の有効なプロキシ
    # {"host": "invalid-proxy", "port": 9999}, # 例: 存在しないプロキシ (エラーテスト用)
]

# ProxyInfo オブジェクトのリストに変換
proxy_list: list[ProxyInfo] = []
for p in proxy_definitions:
    try:
        proxy_list.append(ProxyInfo(host=p["host"], port=p["port"]))
    except (KeyError, ValueError) as e:
        print(f"Warning: Skipping invalid proxy definition {p}: {e}")


def run_screenshot_process():
    """プロキシリストを使ってスクリーンショットを取得するメイン処理"""

    # 1. ロギングを設定
    # 環境変数 LOG_LEVEL=DEBUG などで詳細ログを出力可能
    setup_logging()
    logger = get_logger()  # アプリケーションロガーを取得

    logger.info("--- Starting Screenshot Process ---")
    logger.info(f"Target URL: {TARGET_IP_CHECK_URL}")
    logger.info(f"Found {len(proxy_list)} proxies to test.")

    if not proxy_list:
        logger.warning("No valid proxies defined. Exiting.")
        return

    # 2. 依存関係を準備
    provider = ListProxyProvider(proxy_list)
    selector = ProxySelector(provider)
    # EdgeOptionFactory には --ignore-certificate-errors が含まれている想定
    factory = EdgeOptionFactory()

    # 3. 各プロキシでループ処理
    for index, proxy_info in enumerate(proxy_list):
        logger.info(
            f"--- Processing Proxy #{index}: {proxy_info.host}:{proxy_info.port} ---")

        # ファイル名を一意にする（インデックスとホスト/ポートを含む）
        # ファイル名に使えない文字を置換するなどの処理を追加するとより堅牢
        safe_host = proxy_info.host.replace(".", "_")
        screenshot_filename = f"ip_check_proxy_{index}_{safe_host}_{proxy_info.port}.png"
        screenshot_path_container = os.path.join(
            SCREENSHOT_DIR_CONTAINER, screenshot_filename)

        # ProxiedEdgeBrowser を 'with' 文で使用して自動的にクリーンアップ
        try:
            with ProxiedEdgeBrowser(
                proxy_selector=selector,
                option_factory=factory,
                command_executor=SELENIUM_URL,
                logger=logger  # 同じロガーを渡す
            ) as browser_manager:

                # 4. ブラウザを起動
                browser_manager.start_browser(proxy_index=index)

                # 5. スクリーンショットを取得
                browser_manager.take_screenshot(
                    url=TARGET_IP_CHECK_URL,
                    save_path_in_container=screenshot_path_container
                )
                logger.info(
                    f"Successfully processed proxy #{index}. Screenshot saved.")

                # (任意) 少し待機して次のプロキシへ
                sleep(1)

        except Exception as e:
            # 特定のプロキシでエラーが発生しても処理を続行
            # トレースバックは省略する場合
            logger.error(
                f"Failed to process proxy #{index} ({proxy_info.host}:{proxy_info.port}): {e}", exc_info=False)
            # 詳細が必要な場合は exc_info=True
            logger.warning(f"Skipping proxy #{index} due to error.")
            continue  # 次のループへ

    logger.info("--- Screenshot Process Finished ---")
    print(
        f"\nProcess finished. Check the '{SCREENSHOT_DIR_CONTAINER}' directory inside the container (mapped to './screenshots' on host).")


if __name__ == "__main__":
    run_screenshot_process()
