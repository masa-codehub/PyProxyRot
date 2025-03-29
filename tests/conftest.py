# tests/conftest.py (新規作成または追記)
import pytest
import os
from typing import List  # ListProxyProvider で必要
from src.domain.proxy_info import ProxyInfo
from src.application.proxy_provider import ListProxyProvider
from src.application.proxy_selector import ProxySelector
from src.adapters.edge_option_factory import EdgeOptionFactory
from src.application.proxied_edge_browser import ProxiedEdgeBrowser


@pytest.fixture(scope="session")
def selenium_command_executor():
    """環境変数から Selenium Hub の URL を取得するフィクスチャ"""
    url = os.getenv('SELENIUM_HUB', 'http://selenium:4444/wd/hub')
    print(f"\n[Fixture] Using Selenium Hub URL: {url}")
    return url


@pytest.fixture(scope="session")
def integration_proxy_list():
    """結合テストで使用するプロキシ情報リストを提供するフィクスチャ"""
    # docker-compose のサービス名とポート、または実際のテスト用プロキシを指定
    proxy_host = os.getenv("INTEGRATION_PROXY_HOST", "proxy-server")
    proxy_port_str = os.getenv("INTEGRATION_PROXY_PORT", "8080")
    try:
        proxy_port = int(proxy_port_str)
        print(
            f"\n[Fixture] Using Integration Proxy: {proxy_host}:{proxy_port}")
        return [ProxyInfo(host=proxy_host, port=proxy_port)]
    except (ValueError, TypeError):
        print(
            f"\n[Fixture] Warning: Invalid integration proxy port '{proxy_port_str}'. Returning empty list.")
        return []

# スコープを function に変更し、各テスト後にブラウザを閉じるようにする


@pytest.fixture(scope="function")
def browser_manager_integration(selenium_command_executor, integration_proxy_list):
    """実際の依存関係を持つ ProxiedEdgeBrowser インスタンスを提供するフィクスチャ (結合テスト用)"""
    if not integration_proxy_list:  # プロキシリストが空ならテストをスキップ
        pytest.skip(
            "Integration proxy list is empty or invalid. Skipping integration test.")

    # 実際のクラスを使ってインスタンス化
    provider = ListProxyProvider(integration_proxy_list)
    selector = ProxySelector(provider)
    # EdgeOptionFactory には --ignore-certificate-errors が含まれていると想定
    factory = EdgeOptionFactory()

    manager = ProxiedEdgeBrowser(
        proxy_selector=selector,
        option_factory=factory,
        command_executor=selenium_command_executor
        # デフォルトロガーを使用
    )
    # テスト関数に manager インスタンスを渡す
    yield manager
    # --- テスト関数終了後の後処理 ---
    print("\n[Fixture Teardown] Closing browser...")
    manager.close_browser()
    print("[Fixture Teardown] Browser closed.")
