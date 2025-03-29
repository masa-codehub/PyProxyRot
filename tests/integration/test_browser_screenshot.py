# tests/integration/test_browser_screenshot.py (新規作成または追記)
import pytest
from pathlib import Path
import os
from src.application.proxied_edge_browser import ProxiedEdgeBrowser  # 型チェック用

# integration マークを付ける
pytestmark = pytest.mark.integration

# ホスト側のスクリーンショット保存ディレクトリ
HOST_SCREENSHOT_DIR = Path("./screenshots")


@pytest.fixture(autouse=True)
def ensure_host_screenshot_dir():
    """ホスト側にスクリーンショットディレクトリがなければ作成する"""
    HOST_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def test_take_screenshot_integration(browser_manager_integration: ProxiedEdgeBrowser):
    """
    実際のDocker環境で take_screenshot が機能し、ホストにファイルが保存されるか確認。
    """
    # Arrange
    manager = browser_manager_integration
    proxy_index = 0  # 最初のプロキシを使用
    target_url = "https://example.com/"  # スクリーンショットを撮る対象URL
    # コンテナ内の保存パス (docker-compose.yml でホストの ./screenshots にマウントされている)
    container_save_path = "/app/screenshots/integration_test_screenshot.png"
    # ホスト側の期待されるファイルパス
    host_save_path = HOST_SCREENSHOT_DIR / "integration_test_screenshot.png"

    # 事前にホスト側のファイルが存在すれば削除しておく
    if host_save_path.exists():
        host_save_path.unlink()

    # Act
    try:
        print(f"\n[Integration Test] Starting browser for screenshot...")
        manager.start_browser(proxy_index)
        assert manager._driver is not None, "Browser did not start"
        print(
            f"[Integration Test] Calling take_screenshot({target_url}, {container_save_path})...")
        manager.take_screenshot(
            url=target_url, save_path_in_container=container_save_path)
        print("[Integration Test] take_screenshot completed.")
    except Exception as e:
        pytest.fail(f"take_screenshot raised an unexpected exception: {e}")

    # Assert
    # ホスト側にファイルが作成されたか確認
    assert host_save_path.is_file(
    ), f"Screenshot file was not found on host at {host_save_path}"
    # ファイルサイズが0より大きいか確認 (オプション)
    assert host_save_path.stat().st_size > 0, "Screenshot file is empty"

    # クリーンアップ (テスト後にファイルを削除)
    if host_save_path.exists():
        host_save_path.unlink()

    # ブラウザの終了は browser_manager_integration fixture が行う
