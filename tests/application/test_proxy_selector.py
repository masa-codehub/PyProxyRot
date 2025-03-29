# tests/application/test_proxy_selector.py
import pytest
from typing import List

# --- 依存クラス/インターフェースを import ---
from src.domain.proxy_info import ProxyInfo
from src.application.proxy_provider import ProxyProvider

# --- テスト対象クラスを import (まだ存在しない or 不完全でもOK) ---
# この import が成功するためには、最終的に src/application/proxy_selector.py が必要です。
# from src.application.proxy_selector import ProxySelector

# --- テスト用データ ---
PROXY_LIST_SAMPLE: List[ProxyInfo] = [
    ProxyInfo(host="proxy1.com", port=8001),
    ProxyInfo(host="proxy2.com", port=8002),
    ProxyInfo(host="proxy3.com", port=8003),
]

# --- テスト ---

def test_proxy_selector_selects_correct_proxy(mocker):
    """ProxySelectorが指定されたインデックスのProxyInfoを正しく返すことを確認"""
    # Arrange
    # ProxyProvider のモックを作成し、get_proxiesの戻り値を設定
    mock_provider = mocker.Mock(spec=ProxyProvider)
    mock_provider.get_proxies.return_value = PROXY_LIST_SAMPLE

    # 実際のクラスをインポート (実装後に成功する想定)
    from src.application.proxy_selector import ProxySelector
    selector = ProxySelector(provider=mock_provider)

    # Act & Assert
    # 有効なインデックスでテスト
    assert selector.select_proxy(0) == PROXY_LIST_SAMPLE[0]
    assert selector.select_proxy(1) == PROXY_LIST_SAMPLE[1]
    assert selector.select_proxy(2) == PROXY_LIST_SAMPLE[2] # リストの最後の要素

    # get_proxies が期待通り呼ばれたか確認
    assert mock_provider.get_proxies.call_count == 3

def test_proxy_selector_raises_index_error_for_out_of_bounds(mocker):
    """範囲外のインデックスが指定された場合にIndexErrorを送出することを確認"""
    # Arrange
    mock_provider = mocker.Mock(spec=ProxyProvider)
    mock_provider.get_proxies.return_value = PROXY_LIST_SAMPLE

    from src.application.proxy_selector import ProxySelector
    selector = ProxySelector(provider=mock_provider)

    # Act & Assert
    with pytest.raises(IndexError, match="Proxy index out of range"):
        selector.select_proxy(-1) # 負のインデックス

    with pytest.raises(IndexError, match="Proxy index out of range"):
        selector.select_proxy(len(PROXY_LIST_SAMPLE)) # 範囲外 (リスト長と同じ値)

    with pytest.raises(IndexError, match="Proxy index out of range"):
        selector.select_proxy(100) # 大きすぎるインデックス

def test_proxy_selector_raises_index_error_for_empty_list(mocker):
    """ProxyProviderが空リストを返した場合にIndexErrorを送出することを確認"""
    # Arrange
    mock_provider = mocker.Mock(spec=ProxyProvider)
    mock_provider.get_proxies.return_value = [] # 空リストを設定

    from src.application.proxy_selector import ProxySelector
    selector = ProxySelector(provider=mock_provider)

    # Act & Assert
    with pytest.raises(IndexError, match="Proxy list is empty"):
        selector.select_proxy(0) # どのインデックスでもエラーになる

def test_proxy_selector_raises_type_error_for_non_integer_index(mocker):
    """インデックスが整数でない場合にTypeErrorを送出することを確認"""
    # Arrange
    mock_provider = mocker.Mock(spec=ProxyProvider)
    mock_provider.get_proxies.return_value = PROXY_LIST_SAMPLE

    from src.application.proxy_selector import ProxySelector
    selector = ProxySelector(provider=mock_provider)

    # Act & Assert
    with pytest.raises(TypeError, match="index must be an integer"):
        selector.select_proxy("0") # 文字列のインデックス

    with pytest.raises(TypeError, match="index must be an integer"):
        selector.select_proxy(1.0) # floatのインデックス

def test_proxy_selector_init_requires_proxy_provider(mocker):
    """コンストラクタがProxyProviderインスタンスでない場合にTypeErrorを送出することを確認"""
    # Arrange
    from src.application.proxy_selector import ProxySelector
    not_a_provider = "I am not a provider"

    # Act & Assert
    with pytest.raises(TypeError, match="provider must be an instance of ProxyProvider"):
        ProxySelector(provider=not_a_provider) # type: ignore

    # 正しい型ならエラーにならないことを確認
    mock_provider = mocker.Mock(spec=ProxyProvider)
    try:
        ProxySelector(provider=mock_provider)
    except TypeError:
        pytest.fail("TypeError raised unexpectedly for valid provider type")