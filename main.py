# main.py (最初のプロキシ(proxy-server)のスクショをスキップする最終版)

import os
import sys
import argparse
import logging
from pathlib import Path
from time import sleep
import re
from typing import List  # load_proxies_from_file の型ヒントで使用

# --- 必要なクラス/関数を src からインポート ---
try:
    from src.domain.proxy_info import ProxyInfo
    from src.application.proxy_provider import ListProxyProvider, ProxyProvider
    from src.application.proxy_selector import ProxySelector
    from src.adapters.edge_option_factory import EdgeOptionFactory
    from src.application.proxied_edge_browser import ProxiedEdgeBrowser
    from src.config.logging_config import setup_logging, get_logger
    # webdriver と EdgeOptions は ProxiedEdgeBrowser 内で使われる
    from selenium import webdriver
    from selenium.webdriver.edge.options import Options as EdgeOptions
except ImportError as e:
    print(f"ERROR: Could not import necessary modules from src: {e}")
    print("Make sure PYTHONPATH is set correctly or run from the project root.")
    sys.exit(1)

# --- 設定 ---
SELENIUM_URL = os.getenv('SELENIUM_HUB', 'http://selenium:4444/wd/hub')
DEFAULT_IP_CHECK_URL = "https://ipinfo.io/what-is-my-ip"
DEFAULT_PROXY_FILE = "proxies.txt"
# ★ 最初の行に必須のプロキシホスト名を定義 ★
REQUIRED_FIRST_PROXY_HOST = "proxy-server"
# デフォルトプロキシデータ (ファイルが見つからない場合のフォールバック用)
DEFAULT_PROXIES_DATA = [
    {"host": REQUIRED_FIRST_PROXY_HOST, "port": 8080}  # デフォルトも合わせる
]
SCREENSHOT_DIR_CONTAINER = "/app/screenshots"


def load_proxies_from_file(filepath: str | Path) -> list[ProxyInfo]:
    """指定されたファイルパスからプロキシリストを読み込みます。(変更なし)"""
    proxies: list[ProxyInfo] = []
    file_path = Path(filepath)
    if not file_path.is_file():
        print(f"警告: プロキシファイル '{filepath}' が見つかりません。")
        return []
    print(f"プロキシファイルを読み込みます: {filepath}")
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts: list[str] = []
                if ',' in line:
                    parts = [p.strip() for p in line.split(',', 1)]
                elif ':' in line:
                    parts = [p.strip() for p in line.split(':', 1)]
                if len(parts) == 2:
                    host, port_str = parts
                    try:
                        port = int(port_str)
                        if host and 0 < port < 65536:
                            proxies.append(ProxyInfo(host=host, port=port))
                        else:
                            print(
                                f"警告: ファイル {filepath} の {line_num}行目: 不正なデータです (Host: '{host}', Port: '{port}')。スキップします。")
                    except ValueError:
                        print(
                            f"警告: ファイル {filepath} の {line_num}行目: ポート番号が不正です ('{port_str}')。スキップします。")
                else:
                    print(
                        f"警告: ファイル {filepath} の {line_num}行目: フォーマットが不正です ('{line}')。'host:port' または 'host,port' 形式で記述してください。スキップします。")
    except Exception as e:
        print(f"プロキシファイル '{filepath}' の読み込み中にエラーが発生しました: {e}")
        return []
    return proxies


def main():
    """メインの処理を実行する関数"""
    # --- コマンドライン引数の設定 (変更なし) ---
    parser = argparse.ArgumentParser(
        # 説明更新
        description="プロキシリストファイル(1行目はproxy-server必須)から読み込み、IP確認サイトのスクショを保存。"
    )
    parser.add_argument('-f', '--file', default=DEFAULT_PROXY_FILE,
                        help=f'プロキシリストのファイルパス (デフォルト: {DEFAULT_PROXY_FILE})', metavar='FILEPATH')
    parser.add_argument('-l', '--level', default=os.getenv('LOG_LEVEL', 'INFO').upper(),
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='ログレベルを指定します。')
    parser.add_argument('-u', '--url', default=DEFAULT_IP_CHECK_URL,
                        help=f'IPアドレス確認に使用するURL (デフォルト: {DEFAULT_IP_CHECK_URL})。')
    args = parser.parse_args()

    # --- ロギング設定 ---
    setup_logging(log_level_override=args.level)
    logger = get_logger()

    logger.info("--- 全プロキシ スクリーンショット取得アプリケーション開始 (要件: 1行目は 'proxy-server') ---")

    # --- プロキシリストの準備 ---
    proxy_list = load_proxies_from_file(args.file)

    # --- ★★★ 最初のプロキシが 'proxy-server' か検証する処理を追加 ★★★ ---
    if not proxy_list:
        # ファイル読み込み失敗時のフォールバック処理 (変更なし)
        logger.warning(
            f"ファイル '{args.file}' からプロキシを読み込めなかったか、ファイルが空でした。デフォルトリスト ({REQUIRED_FIRST_PROXY_HOST}) を試します。")
        # ... (フォールバック処理) ...
    else:
        # 最初のプロキシのホスト名を取得し、念のため再度strip()
        first_proxy_host = proxy_list[0].host.strip()
        # コード内の定数も念のためstrip()するなら .strip() を追加
        required_host = REQUIRED_FIRST_PROXY_HOST
        # デバッグ用に比較対象の文字列表現と長さをログ出力
        logger.debug(
            f"最初のプロキシ検証: 検出='{first_proxy_host}' (長さ:{len(first_proxy_host)}), 要求='{required_host}' (長さ:{len(required_host)})")

        # strip() した値で比較
        if first_proxy_host != required_host:
            logger.error(
                f"プロキシファイル '{args.file}' の最初の行のホスト名が '{required_host}' ではありません。")
            logger.error(f"検出されたホスト名: '{first_proxy_host}'")
            # さらに詳細なデバッグ情報（バイト表現）
            logger.error(
                f"要求ホスト バイト: {required_host.encode('utf-8', 'replace')}")
            logger.error(
                f"検出ホスト バイト: {first_proxy_host.encode('utf-8', 'replace')}")
            logger.error(
                f"ファイルを修正して、1行目を '{required_host}:<ポート番号>' にしてください。処理を終了します。")
            sys.exit(1)

    # ★★★ 検証ここまで ★★★

    logger.info(
        f"{len(proxy_list)} 件のプロキシを処理します。Proxy #0 ({REQUIRED_FIRST_PROXY_HOST}) は初期化のみに使用します。")

    # --- 依存コンポーネントの準備 (変更なし) ---
    provider = ListProxyProvider(proxy_list)
    selector = ProxySelector(provider)
    factory = EdgeOptionFactory()  # --ignore-certificate-errors 込みと想定

    # --- 全プロキシでループし、最初のプロキシのスクショはスキップ ---
    success_count = 0  # 処理試行の成功数 (ブラウザ起動成功)
    failure_count = 0  # 処理試行の失敗数
    screenshots_taken = 0  # 実際に保存されたスクショ数

    for i, current_proxy in enumerate(proxy_list):
        logger.info(
            f"--- Processing Proxy #{i}: {current_proxy.host}:{current_proxy.port} ---")

        try:
            # ProxiedEdgeBrowser を 'with' 文で使用
            with ProxiedEdgeBrowser(
                proxy_selector=selector,
                option_factory=factory,
                command_executor=SELENIUM_URL,
                logger=logger
            ) as browser_manager:

                # 1. ブラウザ起動 (常に実行)
                browser_manager.start_browser(proxy_index=i)
                # ブラウザ起動が成功した時点で success_count を増やす
                success_count += 1

                # ★★★ 条件分岐: 最初のプロキシ(index 0)はスクショをスキップ ★★★
                if i == 0:
                    logger.info(
                        f"Skipping screenshot for the first proxy ({current_proxy.host}). Used for initialization.")
                    # 特に何もしない
                else:
                    # 2. スクリーンショット取得 (最初のプロキシ以外)
                    safe_host = re.sub(r'[^\w\-.]', '_', current_proxy.host)
                    screenshot_filename = f"ip_check_proxy_{i}_{safe_host}_{current_proxy.port}.png"
                    screenshot_path_container = os.path.join(
                        SCREENSHOT_DIR_CONTAINER, screenshot_filename)

                    browser_manager.take_screenshot(
                        url=args.url,
                        save_path_in_container=screenshot_path_container
                    )
                    screenshots_taken += 1  # スクショが成功した場合のみカウント
                # ★★★ 分岐ここまで ★★★

        except Exception as e:
            # ブラウザ起動失敗なども含め、このプロキシでの処理が失敗した場合
            logger.error(
                f"Failed to process proxy #{i} ({current_proxy.host}:{current_proxy.port}): {e}", exc_info=False)
            failure_count += 1
            # with ブロックは抜けるので close_browser は呼ばれる
            continue  # 次のプロキシへ

        # 任意: プロキシ間の待機時間
        if i < len(proxy_list) - 1:
            logger.debug("Waiting a bit before next proxy...")
            sleep(1)

    # --- 最終結果表示 ---
    print("-" * 30)
    logger.info("--- Screenshot Process Finished ---")
    print(
        f"Processed {len(proxy_list)} proxies (Proxy #0 was for initialization).")
    print(f"Successful processing attempts (browser started): {success_count}")
    print(f"Actual screenshots taken (Proxy #1 onwards): {screenshots_taken}")
    print(f"Failed attempts: {failure_count}")
    print(f"Check the '{SCREENSHOT_DIR_CONTAINER}' directory inside the container (mapped to './screenshots' on host) for the images (index 1 onwards recommended).")
    print("-" * 30)
    sys.exit(0)


if __name__ == "__main__":
    main()
