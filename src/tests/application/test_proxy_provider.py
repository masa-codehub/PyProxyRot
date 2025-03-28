# tests/application/test_proxy_provider.py (修正後)
import pytest
from typing import List, Any
from abc import ABCMeta  # ProxyProviderがABCであることを確認するために使用

# --- 依存するクラスを src から import ---
from src.domain.proxy_info import ProxyInfo

# --- テスト対象のモジュールを import ---
from src.application.proxy_provider import ProxyProvider, ListProxyProvider

# --- テストコード本体 (変更なし) ---


def test_list_proxy_provider_initialization_and_get_proxies():
    # ... (省略) ...
    proxy_list_data: List[ProxyInfo] = [
        ProxyInfo(host="127.0.0.1", port=8080),
        ProxyInfo(host="192.168.1.1", port=3128),
    ]
    provider = ListProxyProvider(proxy_list_data)
    retrieved_list = provider.get_proxies()
    assert retrieved_list == proxy_list_data
    assert id(retrieved_list) == id(proxy_list_data)


def test_list_proxy_provider_with_empty_list():
    # ... (省略) ...
    proxy_list_data: List[ProxyInfo] = []
    provider = ListProxyProvider(proxy_list_data)
    retrieved_list = provider.get_proxies()
    assert retrieved_list == []


def test_list_proxy_provider_requires_list_of_proxy_info():
    # ... (省略) ...
    invalid_list_item: List[Any] = [
        ProxyInfo(host="127.0.0.1", port=8080),
        "not a proxy info",
    ]
    invalid_list_type = {"host": "127.0.0.1", "port": 8080}
    valid_list: List[ProxyInfo] = [ProxyInfo(host="127.0.0.1", port=8080)]

    with pytest.raises(TypeError, match="All items in proxy_list must be ProxyInfo instances"):
        ListProxyProvider(invalid_list_item)
    with pytest.raises(TypeError, match="proxy_list must be a list"):
        ListProxyProvider(invalid_list_type)  # type: ignore
    try:
        ListProxyProvider(valid_list)
    except TypeError:
        pytest.fail("TypeError raised unexpectedly for valid list")


def test_list_proxy_provider_implements_proxy_provider_interface():
    # ... (省略) ...
    proxy_list_data: List[ProxyInfo] = [ProxyInfo(host="127.0.0.1", port=8080)]
    provider = ListProxyProvider(proxy_list_data)
    assert isinstance(provider, ProxyProvider)
    assert hasattr(provider, 'get_proxies')
    assert callable(provider.get_proxies)
