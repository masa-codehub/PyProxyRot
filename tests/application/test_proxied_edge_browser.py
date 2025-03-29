# tests/application/test_proxied_edge_browser.py
import pytest
import logging
from unittest.mock import MagicMock  # mocker だけでなく MagicMock も直接使える
from typing import List, Optional  # <<< この行を追加または確認
from types import TracebackType  # __exit__で使う場合 (もし追加していれば)


# モック対象のクラスとテスト対象クラスをインポート
# 実際の依存関係の解決は pytest が行う (PYTHONPATH設定や __init__.py が適切なら)
from src.application.proxy_selector import ProxySelector
from src.adapters.edge_option_factory import EdgeOptionFactory
from src.application.proxied_edge_browser import ProxiedEdgeBrowser
from src.application.proxy_provider import ProxyProvider  # ProxySelector の spec に必要
from src.domain.proxy_info import ProxyInfo  # ダミーデータ作成に必要

# --- 基本構造とインスタンス化のテスト (Issue #8) ---


def test_proxied_edge_browser_instantiation(mocker):
    """ProxiedEdgeBrowser がモック化された依存性でインスタンス化できることをテスト"""
    # Arrange
    # 依存コンポーネントのモックを作成
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
        pytest.fail(f"インスタンス化中に予期せぬエラー: {e}")

    # Assert
    assert isinstance(browser_manager, ProxiedEdgeBrowser)
    # 内部属性に依存性が保存されているか確認 (_ はプライベート属性の慣習)
    assert browser_manager._selector is mock_selector
    assert browser_manager._option_factory is mock_factory
    assert browser_manager._command_executor == dummy_url
    assert browser_manager._logger is mock_logger
    assert browser_manager._driver is None  # 初期状態では driver は None


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
        # logger 引数を省略
    )

    # Assert
    # デフォルトロガーが取得されているか型で確認
    assert isinstance(browser_manager._logger, logging.Logger)


def test_proxied_edge_browser_raises_type_error_for_invalid_dependencies(mocker):
    """不正な型の依存性を渡した場合に TypeError が発生することをテスト"""
    # Arrange
    mock_selector = mocker.Mock(spec=ProxySelector)
    mock_factory = mocker.Mock(spec=EdgeOptionFactory)
    dummy_url = "http://fake-selenium-hub:4444/wd/hub"
    invalid_selector = "これはセレクターではない"
    invalid_factory = "これはファクトリではない"

    # Act & Assert
    with pytest.raises(TypeError, match="proxy_selector は ProxySelector のインスタンスである必要があります"):
        ProxiedEdgeBrowser(invalid_selector, mock_factory,
                           dummy_url)  # type: ignore

    with pytest.raises(TypeError, match="option_factory は EdgeOptionFactory のインスタンスである必要があります"):
        ProxiedEdgeBrowser(mock_selector, invalid_factory,
                           dummy_url)  # type: ignore


def test_proxied_edge_browser_raises_value_error_for_empty_executor(mocker):
    """command_executor が空または None の場合に ValueError が発生することをテスト"""
    # Arrange
    mock_selector = mocker.Mock(spec=ProxySelector)
    mock_factory = mocker.Mock(spec=EdgeOptionFactory)

    # Act & Assert
    with pytest.raises(ValueError, match="command_executor URL は空にできず、文字列である必要があります"):
        ProxiedEdgeBrowser(mock_selector, mock_factory, "")  # 空文字列

    with pytest.raises(ValueError, match="command_executor URL は空にできず、文字列である必要があります"):
        ProxiedEdgeBrowser(mock_selector, mock_factory,
                           None)  # type: ignore # None


def test_proxied_edge_browser_has_method_stubs(mocker):
    """要求されたメソッドスタブが存在し、呼び出し可能であることを確認"""
    # Arrange
    # コンストラクタの型チェックをパスするための具体的なモック/ダミー
    class MockProxyProvider(ProxyProvider):  # ProxyProviderを継承したダミークラス
        def get_proxies(self) -> List[ProxyInfo]: return []
    mock_selector = ProxySelector(MockProxyProvider())  # 実際のクラスを使う (依存性が必要)
    mock_factory = EdgeOptionFactory()                 # 実際のクラスを使う
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
    # コンテキストマネージャ用メソッド
    assert hasattr(browser_manager, '__enter__')
    assert callable(browser_manager.__enter__)
    assert hasattr(browser_manager, '__exit__')
    assert callable(browser_manager.__exit__)
