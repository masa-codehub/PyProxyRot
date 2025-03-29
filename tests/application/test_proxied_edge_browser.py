# tests/application/test_proxied_edge_browser.py (修正・整理版)

import pytest
import logging
from unittest.mock import MagicMock, patch
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
# from typing import List # ← list[...] を使うので不要になる

# 必要なクラス/インターフェースをインポート
from src.domain.proxy_info import ProxyInfo
from src.application.proxy_selector import ProxySelector
from src.adapters.edge_option_factory import EdgeOptionFactory
from src.application.proxied_edge_browser import ProxiedEdgeBrowser
from src.application.proxy_provider import ProxyProvider

# --- 基本構造とインスタンス化のテスト (Issue #8) ---


def test_proxied_edge_browser_instantiation(mocker):
    """ProxiedEdgeBrowser がモック化された依存性でインスタンス化できることをテスト"""
    # Arrange
    mock_selector = mocker.Mock(spec=ProxySelector)
    mock_factory = mocker.Mock(spec=EdgeOptionFactory)
    mock_logger = mocker.Mock(spec=logging.Logger)
    dummy_url = "http://fake-selenium-hub:4444/wd/hub"

    # Act
    try:
        browser_manager = ProxiedEdgeBrowser(
            proxy_selector=mock_selector,
            option_factory=mock_factory,
            command_executor=dummy_url,
            logger=mock_logger
        )
    except Exception as e:
        pytest.fail(f"Instantiation failed unexpectedly: {e}")  # メッセージを英語に

    # Assert
    assert isinstance(browser_manager, ProxiedEdgeBrowser)
    assert browser_manager._selector is mock_selector
    assert browser_manager._option_factory is mock_factory
    assert browser_manager._command_executor == dummy_url
    assert browser_manager._logger is mock_logger
    assert browser_manager._driver is None


def test_proxied_edge_browser_instantiation_with_default_logger(mocker):
    """デフォルトロガーを使用してインスタンス化できることをテスト"""
    # Arrange
    mock_selector = mocker.Mock(spec=ProxySelector)
    mock_factory = mocker.Mock(spec=EdgeOptionFactory)
    dummy_url = "http://fake-selenium-hub:4444/wd/hub"

    # Act
    browser_manager = ProxiedEdgeBrowser(
        proxy_selector=mock_selector,
        option_factory=mock_factory,
        command_executor=dummy_url
    )

    # Assert
    assert isinstance(browser_manager._logger, logging.Logger)


def test_proxied_edge_browser_raises_type_error_for_invalid_dependencies(mocker):
    """不正な型の依存性を渡した場合に TypeError が発生することをテスト"""
    # Arrange
    mock_selector = mocker.Mock(spec=ProxySelector)
    mock_factory = mocker.Mock(spec=EdgeOptionFactory)
    dummy_url = "http://fake-selenium-hub:4444/wd/hub"
    invalid_selector = "not a selector"
    invalid_factory = "not a factory"

    # Act & Assert
    # エラーメッセージも実装コードに合わせて英語でチェック
    with pytest.raises(TypeError, match="proxy_selector must be an instance of ProxySelector"):
        ProxiedEdgeBrowser(invalid_selector, mock_factory,
                           dummy_url)  # type: ignore

    with pytest.raises(TypeError, match="option_factory must be an instance of EdgeOptionFactory"):
        ProxiedEdgeBrowser(mock_selector, invalid_factory,
                           dummy_url)  # type: ignore


def test_proxied_edge_browser_raises_value_error_for_empty_executor(mocker):
    """command_executor が空または None の場合に ValueError が発生することをテスト"""
    # Arrange
    mock_selector = mocker.Mock(spec=ProxySelector)
    mock_factory = mocker.Mock(spec=EdgeOptionFactory)

    # Act & Assert
    # エラーメッセージも実装コードに合わせて英語でチェック
    with pytest.raises(ValueError, match="command_executor URL cannot be empty and must be a string"):
        ProxiedEdgeBrowser(mock_selector, mock_factory, "")

    with pytest.raises(ValueError, match="command_executor URL cannot be empty and must be a string"):
        ProxiedEdgeBrowser(mock_selector, mock_factory, None)  # type: ignore


def test_proxied_edge_browser_has_method_stubs(mocker):
    """要求されたメソッドスタブが存在し、呼び出し可能であることを確認"""
    # Arrange
    class MockProxyProvider(ProxyProvider):
        # ★ 型ヒントを list に変更 ★
        def get_proxies(self) -> list[ProxyInfo]: return []
    mock_selector = ProxySelector(MockProxyProvider())
    mock_factory = EdgeOptionFactory()
    dummy_url = "http://fake-selenium-hub:4444/wd/hub"

    browser_manager = ProxiedEdgeBrowser(
        mock_selector, mock_factory, dummy_url)

    # Assert
    assert hasattr(browser_manager, 'start_browser')
    assert callable(browser_manager.start_browser)
    assert hasattr(browser_manager, 'take_screenshot')
    assert callable(browser_manager.take_screenshot)
    assert hasattr(browser_manager, 'close_browser')
    assert callable(browser_manager.close_browser)
    assert hasattr(browser_manager, '__enter__')
    assert callable(browser_manager.__enter__)
    assert hasattr(browser_manager, '__exit__')
    assert callable(browser_manager.__exit__)

# --- start_browser のユニットテスト ---


@pytest.fixture
def browser_manager_mocks(mocker):
    """モック化された依存性を持つ ProxiedEdgeBrowser インスタンスを提供するフィクスチャ"""
    mock_selector = mocker.Mock(spec=ProxySelector)
    mock_factory = mocker.Mock(spec=EdgeOptionFactory)
    mock_logger = mocker.Mock(spec=logging.Logger)
    dummy_url = "http://fake-selenium-hub:4444/wd/hub"

    mock_selector.select_proxy.return_value = ProxyInfo(
        host="mock.proxy", port=1234)
    mock_options = mocker.Mock(spec=EdgeOptions)
    mock_factory.create_options.return_value = mock_options

    manager = ProxiedEdgeBrowser(
        proxy_selector=mock_selector,
        option_factory=mock_factory,
        command_executor=dummy_url,
        logger=mock_logger
    )
    mock_remote_class = mocker.patch(
        'src.application.proxied_edge_browser.webdriver.Remote')
    mock_driver_instance = mocker.Mock(spec=RemoteWebDriver)
    mock_driver_instance.session_id = "mock_session_123"
    mock_remote_class.return_value = mock_driver_instance
    manager.close_browser = mocker.Mock()

    return manager, mock_selector, mock_factory, mock_logger, mock_remote_class, mock_options


def test_start_browser_success(browser_manager_mocks):
    """start_browser が成功するケースをテスト"""
    # Arrange
    manager, mock_selector, mock_factory, mock_logger, mock_remote_class, mock_options = browser_manager_mocks
    proxy_index = 0
    expected_proxy_info = ProxyInfo(host="mock.proxy", port=1234)
    mock_selector.select_proxy.return_value = expected_proxy_info

    # Act
    manager.start_browser(proxy_index)

    # Assert
    manager.close_browser.assert_not_called()  # 既存ドライバがなければ呼ばれない
    mock_selector.select_proxy.assert_called_once_with(proxy_index)
    mock_factory.create_options.assert_called_once_with(expected_proxy_info)
    mock_remote_class.assert_called_once_with(
        command_executor=manager._command_executor,
        options=mock_options
    )
    assert manager._driver is mock_remote_class.return_value
    assert manager._driver.session_id == "mock_session_123"
    # ★ ログアサーション (英語) ★
    mock_logger.info.assert_any_call(
        f"Attempting to start browser using proxy index {proxy_index}...")
    mock_logger.info.assert_any_call(
        f"Browser session started successfully. Session ID: mock_session_123")


# ★ mocker 引数を追加 ★
def test_start_browser_closes_existing_session(browser_manager_mocks, mocker):
    """既存セッションがある場合に close_browser が呼ばれることをテスト"""
    # Arrange
    manager, _, _, mock_logger, mock_remote_class, _ = browser_manager_mocks
    manager._driver = mocker.Mock(spec=RemoteWebDriver)  # ★ mocker を使用 ★

    # Act
    manager.start_browser(0)

    # Assert
    manager.close_browser.assert_called_once()
    # ★ ログアサーション (英語) ★
    mock_logger.warning.assert_called_once_with(
        "An active browser session exists. Closing it before starting a new one.")
    mock_remote_class.assert_called_once()
    assert manager._driver is mock_remote_class.return_value


def test_start_browser_handles_select_proxy_index_error(browser_manager_mocks):
    """proxy_selector が IndexError を発生させた場合の処理をテスト"""
    # Arrange
    manager, mock_selector, _, mock_logger, mock_remote_class, _ = browser_manager_mocks
    proxy_index = 99
    mock_selector.select_proxy.side_effect = IndexError("Test index error")

    # Act & Assert
    with pytest.raises(IndexError):
        manager.start_browser(proxy_index)

    # Assert
    mock_remote_class.assert_not_called()
    assert manager._driver is None
    mock_logger.error.assert_called_once()
    args, kwargs = mock_logger.error.call_args
    # ★ ログアサーション (英語) ★
    assert "Failed to prepare for browser start" in args[0]
    assert kwargs.get("exc_info") is True


def test_start_browser_handles_create_options_type_error(browser_manager_mocks):
    """option_factory が TypeError を発生させた場合の処理をテスト"""
    # Arrange
    manager, _, mock_factory, mock_logger, mock_remote_class, _ = browser_manager_mocks
    mock_factory.create_options.side_effect = TypeError("Test type error")

    # Act & Assert
    with pytest.raises(TypeError):
        manager.start_browser(0)

    # Assert
    mock_remote_class.assert_not_called()
    assert manager._driver is None
    mock_logger.error.assert_called_once()
    args, kwargs = mock_logger.error.call_args
    # ★ ログアサーション (英語) ★
    assert "Failed to prepare for browser start" in args[0]
    assert kwargs.get("exc_info") is True


def test_start_browser_handles_webdriver_exception(browser_manager_mocks):
    """webdriver.Remote が WebDriverException を発生させた場合の処理をテスト"""
    # Arrange
    manager, _, _, mock_logger, mock_remote_class, _ = browser_manager_mocks
    mock_remote_class.side_effect = WebDriverException("Test WebDriver error")

    # Act & Assert
    with pytest.raises(WebDriverException):
        manager.start_browser(0)

    # Assert
    mock_remote_class.assert_called_once()
    assert manager._driver is None
    mock_logger.error.assert_called_once()
    args, kwargs = mock_logger.error.call_args
    # ★ ログアサーション (英語) ★
    assert "Failed to start WebDriver session" in args[0]
    assert kwargs.get("exc_info") is True
