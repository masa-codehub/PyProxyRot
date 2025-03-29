# tests/integration/test_browser_context_manager.py (新規作成)
import pytest
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from src.application.proxied_edge_browser import ProxiedEdgeBrowser  # 型チェック用
import time  # セッション確認用

# このファイル内のすべてのテストを 'integration' マークにする
pytestmark = pytest.mark.integration


def test_context_manager_closes_browser_integration(browser_manager_integration: ProxiedEdgeBrowser):
    """
    'with' ステートメントを使用してブラウザを起動・終了できるかを確認する結合テスト。
    """
    # Arrange
    manager = browser_manager_integration
    proxy_index = 0
    initial_session_id = None

    # Act & Assert within context
    print("\n[Integration Test] Entering 'with' block...")
    with manager:
        print("[Integration Test] Starting browser inside 'with'...")
        manager.start_browser(proxy_index)
        print("[Integration Test] Browser started inside 'with'.")
        assert manager._driver is not None, "Driver should be active inside 'with' block"
        initial_session_id = manager._driver.session_id
        assert initial_session_id is not None
        print(f"[Integration Test] Initial Session ID: {initial_session_id}")
        # 必要なら簡単な操作
        # manager._driver.get("about:blank")

    # Assert after context
    print("[Integration Test] Exited 'with' block.")
    assert manager._driver is None, "Driver should be None after exiting 'with' block"

    # オプション: 再度起動して、新しいセッションが作られるか確認
    # (ブラウザの起動/終了は時間がかかる場合がある)
    print("[Integration Test] Attempting to restart browser after 'with' block...")
    try:
        time.sleep(1)  # WebDriver終了を待つ猶予
        manager.start_browser(proxy_index)
        assert manager._driver is not None, "Should be able to restart browser"
        new_session_id = manager._driver.session_id
        assert new_session_id is not None
        assert new_session_id != initial_session_id, "New session should have a different ID"
        print(
            f"[Integration Test] Restarted browser with new Session ID: {new_session_id}")
    except Exception as e:
        pytest.fail(
            f"Failed to restart browser after context manager exit: {e}")

    # クリーンアップは browser_manager_integration fixture が行う (再度呼ばれる)
