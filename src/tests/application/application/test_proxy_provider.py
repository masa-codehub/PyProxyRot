# tests/application/test_proxy_provider.py

import pytest
from typing import List, Any
from abc import ABCMeta  # ProxyProviderがABCであることを確認するために使用

# --- 依存するクラスを src から import ---
# (現時点では存在しないが、最終的に必要になる)
# from src.domain.proxy_info import ProxyInfo
# from src.application.proxy_provider import ProxyProvider, ListProxyProvider

# --- 依存するクラスの仮定義（テスト先行のため） ---
from dataclasses import dataclass


@dataclass(frozen=True)
class ProxyInfo:
    host: str
    port: int


class ProxyProvider(metaclass=ABCMeta):  # ABCとして仮定義
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'get_proxies') and
                callable(subclass.get_proxies))


class ListProxyProvider:  # 実装クラスとして仮定義
    def __init__(self, proxy_list): pass
    def get_proxies(self): pass
# --- ここまで仮定義 ---


def test_list_proxy_provider_initialization_and_get_proxies():
    """ListProxyProviderがProxyInfoのリストで初期化され、get_proxiesがそのリストを返すことを確認"""
    # Arrange
    # --- 実際のクラスを import するように変更 ---
    from src.application.proxy_provider import ListProxyProvider
    # --- ここで ProxyInfo も src から import する想定だが、仮定義を使う ---
    # from src.domain.proxy_info import ProxyInfo

    proxy_list_data: List[ProxyInfo] = [
        ProxyInfo(host="127.0.0.1", port=8080),
        ProxyInfo(host="192.168.1.1", port=3128),
    ]

    # Act
    provider = ListProxyProvider(proxy_list_data)
    retrieved_list = provider.get_proxies()

    # Assert
    assert retrieved_list == proxy_list_data
    # リストがコピーではなく同じ参照であることを確認（今回の仕様）
    assert id(retrieved_list) == id(proxy_list_data)


def test_list_proxy_provider_with_empty_list():
    """空のリストで初期化した場合の動作確認"""
    # Arrange
    from src.application.proxy_provider import ListProxyProvider
    # from src.domain.proxy_info import ProxyInfo
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
    # from src.domain.proxy_info import ProxyInfo
    invalid_list_item: List[Any] = [
        ProxyInfo(host="127.0.0.1", port=8080),
        "not a proxy info",  # Invalid item
    ]
    invalid_list_type = {"host": "127.0.0.1", "port": 8080}  # Not a list
    valid_list: List[ProxyInfo] = [ProxyInfo(host="127.0.0.1", port=8080)]

    # Act & Assert
    with pytest.raises(TypeError, match="All items in proxy_list must be ProxyInfo instances"):
        ListProxyProvider(invalid_list_item)

    with pytest.raises(TypeError, match="proxy_list must be a list"):
        ListProxyProvider(invalid_list_type)  # type: ignore

    # Valid list should not raise TypeError
    try:
        ListProxyProvider(valid_list)
    except TypeError:
        pytest.fail("TypeError raised unexpectedly for valid list")


def test_list_proxy_provider_implements_proxy_provider_interface():
    """ListProxyProviderがProxyProviderインターフェースを実装しているか確認"""
    # Arrange
    from src.application.proxy_provider import ProxyProvider, ListProxyProvider
    # from src.domain.proxy_info import ProxyInfo
    proxy_list_data: List[ProxyInfo] = [ProxyInfo(host="127.0.0.1", port=8080)]
    provider = ListProxyProvider(proxy_list_data)

    # Assert
    # Check if it's a subclass (using ABC)
    assert isinstance(provider, ProxyProvider)
    assert hasattr(provider, 'get_proxies')     # Check if method exists
    assert callable(provider.get_proxies)    # Check if it's callable
