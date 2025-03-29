# tests/integration/test_browser_startup.py (新規作成または編集)
import pytest
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.common.exceptions import WebDriverException
from src.application.proxied_edge_browser import ProxiedEdgeBrowser  # 型チェック用

# このファイル内のすべてのテストを 'integration' マークにする
pytestmark = pytest.mark.integration


def test_start_browser_integration_success(browser_manager_integration: ProxiedEdgeBrowser):
    """
    実際のDocker環境で ProxiedEdgeBrowser.start_browser が
    エラーなくWebDriverセッションを開始できることを確認する結合テスト。
    """
    # Arrange
    manager = browser_manager_integration
    proxy_index = 0  # 最初のプロキシを使用

    # Act
    try:
        print(f"\n[Integration Test] Calling start_browser({proxy_index})...")
        manager.start_browser(proxy_index)
        print("[Integration Test] start_browser completed.")

        # 簡単な操作でセッションが有効か確認 (タイトル取得など)
        print("[Integration Test] Getting browser title...")
        # driver インスタンスが None でないことを確認してからアクセス
        assert manager._driver is not None, "WebDriver instance should not be None after start"
        title = manager._driver.title
        # 空のタイトルなどが返る場合がある
        print(f"[Integration Test] Browser title: '{title}'")

    except WebDriverException as e:
        pytest.fail(
            f"start_browser({proxy_index}) raised WebDriverException unexpectedly: {e}")
    except Exception as e:
        pytest.fail(
            f"start_browser({proxy_index}) raised an unexpected exception: {e}")

    # Assert
    assert manager._driver is not None, "WebDriver instance should be created"
    assert isinstance(
        manager._driver, RemoteWebDriver), "Instance should be RemoteWebDriver"
    assert manager._driver.session_id is not None, "WebDriver session should be active"

    # クリーンアップは fixture の teardown で行われる


def test_start_browser_integration_invalid_index(browser_manager_integration: ProxiedEdgeBrowser):
    """無効なプロキシインデックスを指定した場合にエラーが発生することを確認する結合テスト"""
    # Arrange
    manager = browser_manager_integration
    invalid_proxy_index = 99  # リストに存在しないインデックス

    # Act & Assert
    with pytest.raises((IndexError, TypeError)):  # select_proxy が送出する例外を期待
        print(
            f"\n[Integration Test] Calling start_browser({invalid_proxy_index}) with invalid index...")
        manager.start_browser(invalid_proxy_index)

    # Assert that driver was not created
    assert manager._driver is None, "WebDriver instance should not be created for invalid index"
