# tests/application/test_proxy_provider.py
import pytest
from typing import List, Any
from abc import ABCMeta # インターフェース実装確認用

# --- 依存するクラスを src から import ---
# このテストを実行する前に src/domain/proxy_info.py が存在し、
# ProxyInfo クラスが定義されている必要があります。
from src.domain.proxy_info import ProxyInfo

# --- テスト対象のモジュールを import (まだ存在しない or 不完全でもOK) ---
# この import が成功するためには、最終的に src/application/proxy_provider.py が必要です。
# from src.application.proxy_provider import ProxyProvider, ListProxyProvider

# --- テスト ---

def test_list_proxy_provider_initialization_and_get_proxies():
    """ListProxyProviderがProxyInfoのリストで初期化され、get_proxiesがそのリストを返すことを確認"""
    # Arrange
    # 実際のクラスをインポート (実装後に成功する想定)
    from src.application.proxy_provider import ListProxyProvider

    proxy_list_data: List[ProxyInfo] = [
        ProxyInfo(host="127.0.0.1", port=8080),
        ProxyInfo(host="192.168.1.1", port=3128),
    ]

    # Act
    provider = ListProxyProvider(proxy_list_data)
    retrieved_list = provider.get_proxies()

    # Assert
    assert retrieved_list == proxy_list_data
    # 内部リストの参照をそのまま返す仕様とする (コピーしない)
    assert id(retrieved_list) == id(proxy_list_data)

def test_list_proxy_provider_with_empty_list():
    """空のリストで初期化した場合の動作確認"""
    # Arrange
    from src.application.proxy_provider import ListProxyProvider
    proxy_list_data: List[ProxyInfo] = []

    # Act
    provider = ListProxyProvider(proxy_list_data)
    retrieved_list = provider.get_proxies()

    # Assert
    assert retrieved_list == []

def test_list_proxy_provider_requires_list_of_proxy_info():
    """コンストラクタがProxyInfoのリスト以外を受け付けないことを確認"""
    # Arrange
    from src.application.proxy_provider import ListProxyProvider
    invalid_list_item: List[Any] = [
        ProxyInfo(host="127.0.0.1", port=8080),
        "not a proxy info", # 不正な型の要素
    ]
    invalid_list_type = {"host": "127.0.0.1", "port": 8080} # リストではない
    valid_list: List[ProxyInfo] = [ProxyInfo(host="127.0.0.1", port=8080)]

    # Act & Assert
    # 不正なアイテムが含まれる場合
    with pytest.raises(TypeError, match="All items in proxy_list must be ProxyInfo instances"):
        ListProxyProvider(invalid_list_item)

    # リスト型でない場合
    with pytest.raises(TypeError, match="proxy_list must be a list"):
        ListProxyProvider(invalid_list_type) # type: ignore

    # 正しいリストの場合、エラーが発生しないことを確認
    try:
        ListProxyProvider(valid_list)
    except TypeError:
        pytest.fail("TypeError raised unexpectedly for valid list")

def test_list_proxy_provider_implements_proxy_provider_interface():
    """ListProxyProviderがProxyProviderインターフェースを実装しているか確認"""
    # Arrange
    # インターフェースと実装クラスの両方をインポート (実装後に成功する想定)
    from src.application.proxy_provider import ProxyProvider, ListProxyProvider
    proxy_list_data: List[ProxyInfo] = [ProxyInfo(host="127.0.0.1", port=8080)]
    provider = ListProxyProvider(proxy_list_data)

    # Assert
    assert isinstance(provider, ProxyProvider) # ABCを継承/実装しているか
    assert hasattr(provider, 'get_proxies')     # get_proxies メソッドを持つか
    assert callable(provider.get_proxies)    # get_proxies が呼び出し可能か