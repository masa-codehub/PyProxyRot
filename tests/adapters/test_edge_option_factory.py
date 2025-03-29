# tests/adapters/test_edge_option_factory.py
import pytest
from selenium.webdriver.edge.options import Options as EdgeOptions # SeleniumからEdgeOptionsをインポート

# --- 依存クラスを import ---
# このテストを実行する前に src/domain/proxy_info.py が存在し、
# ProxyInfo クラスが定義されている必要があります。
from src.domain.proxy_info import ProxyInfo

# --- テスト対象クラスを import (まだ存在しない or 不完全でもOK) ---
# この import が成功するためには、最終的に src/adapters/edge_option_factory.py が必要です。
# from src.adapters.edge_option_factory import EdgeOptionFactory

# --- テスト ---

def test_create_options_returns_edge_options_instance():
    """create_options が EdgeOptions インスタンスを返すことを確認"""
    # Arrange
    from src.adapters.edge_option_factory import EdgeOptionFactory # 実装後にインポートされる想定
    proxy_info = ProxyInfo(host="proxy.test.com", port=8888)
    factory = EdgeOptionFactory()

    # Act
    options = factory.create_options(proxy_info)

    # Assert
    assert isinstance(options, EdgeOptions)

def test_create_options_adds_correct_proxy_argument():
    """create_options が正しい --proxy-server 引数を EdgeOptions に追加することを確認"""
    # Arrange
    from src.adapters.edge_option_factory import EdgeOptionFactory
    host = "192.168.1.100"
    port = 3128
    proxy_info = ProxyInfo(host=host, port=port)
    factory = EdgeOptionFactory()
    expected_argument = f"--proxy-server={host}:{port}"

    # Act
    options = factory.create_options(proxy_info)

    # Assert
    # options.arguments で追加された引数リストを確認します。
    # 注意: Selenium のバージョンによっては .arguments 属性の扱いが変わる可能性があります。
    # より確実な方法は .capabilities の内容を確認することですが、まずは arguments で検証します。
    assert hasattr(options, 'arguments'), "EdgeOptions に 'arguments' 属性が存在しません。Seleniumのバージョンを確認してください。"
    assert isinstance(options.arguments, list), "'arguments' 属性がリストではありません。"
    assert expected_argument in options.arguments

def test_create_options_handles_different_proxy_info():
    """異なるProxyInfoに対しても正しく引数を生成することを確認"""
    # Arrange
    from src.adapters.edge_option_factory import EdgeOptionFactory
    proxy_info1 = ProxyInfo(host="proxy1.test", port=1080)
    proxy_info2 = ProxyInfo(host="10.0.0.1", port=8080)
    factory = EdgeOptionFactory()
    expected_arg1 = f"--proxy-server={proxy_info1.host}:{proxy_info1.port}"
    expected_arg2 = f"--proxy-server={proxy_info2.host}:{proxy_info2.port}"

    # Act
    options1 = factory.create_options(proxy_info1)
    options2 = factory.create_options(proxy_info2)

    # Assert
    assert hasattr(options1, 'arguments') and hasattr(options2, 'arguments')
    assert expected_arg1 in options1.arguments
    assert expected_arg2 in options2.arguments

def test_create_options_input_validation():
    """create_options が ProxyInfo 以外の型を受け付けないことを確認"""
    # Arrange
    from src.adapters.edge_option_factory import EdgeOptionFactory
    factory = EdgeOptionFactory()
    invalid_input = "not proxy info"

    # Act & Assert
    with pytest.raises(TypeError, match="proxy_info must be an instance of ProxyInfo"):
        factory.create_options(invalid_input) # type: ignore

    # 正しい型ならエラーにならないことを確認
    try:
        valid_proxy = ProxyInfo(host="valid", port=80)
        factory.create_options(valid_proxy)
    except TypeError:
        pytest.fail("TypeError raised unexpectedly for valid ProxyInfo")