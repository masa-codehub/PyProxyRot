# tests/domain/test_proxy_info.py
import pytest
from dataclasses import FrozenInstanceError

from src.domain.proxy_info import ProxyInfo


def test_proxy_info_initialization_and_attributes():
    """ProxyInfoが正しく初期化され、属性にアクセスできることを確認"""
    # Arrange
    from src.domain.proxy_info import ProxyInfo
    host = "proxy.example.com"
    port = 8080

    # Act
    proxy_info = ProxyInfo(host=host, port=port)

    # Assert
    assert proxy_info.host == host
    assert proxy_info.port == port


def test_proxy_info_immutability():
    """ProxyInfoが不変であることを確認 (属性再代入でエラー)"""
    # Arrange
    from src.domain.proxy_info import ProxyInfo
    proxy_info = ProxyInfo(host="proxy.example.com", port=8080)

    # Act & Assert
    with pytest.raises(FrozenInstanceError):
        proxy_info.host = "new.proxy.com"  # type: ignore

    with pytest.raises(FrozenInstanceError):
        proxy_info.port = 8888  # type: ignore


def test_proxy_info_equality():
    """ProxyInfoの等価性比較が正しく機能することを確認"""
    # Arrange
    from src.domain.proxy_info import ProxyInfo
    info1 = ProxyInfo(host="proxy.example.com", port=8080)
    info2 = ProxyInfo(host="proxy.example.com", port=8080)  # Same values
    info3 = ProxyInfo(host="other.proxy.com", port=8080)  # Different host
    info4 = ProxyInfo(host="proxy.example.com", port=8888)  # Different port

    # Assert
    assert info1 == info2
    assert info1 is not info2  # Different objects
    assert info1 != info3
    assert info1 != info4
    assert info1 != ("proxy.example.com", 8080)  # Different type


def test_proxy_info_host_validation():
    """Host属性のバリデーションが機能することを確認"""
    # Arrange
    from src.domain.proxy_info import ProxyInfo

    # Act & Assert
    with pytest.raises(ValueError, match="Host must be a non-empty string"):
        ProxyInfo(host="", port=8080)  # Empty host

    with pytest.raises(ValueError, match="Host must be a non-empty string"):
        ProxyInfo(host=None, port=8080)  # type: ignore # Invalid type (None)

    with pytest.raises(ValueError, match="Host must be a non-empty string"):
        ProxyInfo(host=123, port=8080)  # type: ignore # Invalid type (int)

    # Valid host should not raise error
    try:
        ProxyInfo(host="valid-host", port=8080)
    except ValueError:
        pytest.fail("ValueError raised unexpectedly for valid host")


def test_proxy_info_port_validation():
    """Port属性のバリデーションが機能することを確認"""
    # Arrange
    from src.domain.proxy_info import ProxyInfo

    # Act & Assert
    with pytest.raises(ValueError, match="Port must be an integer between 1 and 65535"):
        ProxyInfo(host="proxy.example.com", port=0)  # Port too low

    with pytest.raises(ValueError, match="Port must be an integer between 1 and 65535"):
        ProxyInfo(host="proxy.example.com", port=65536)  # Port too high

    with pytest.raises(ValueError, match="Port must be an integer between 1 and 65535"):
        # type: ignore # Invalid type (str)
        ProxyInfo(host="proxy.example.com", port="8080")

    with pytest.raises(ValueError, match="Port must be an integer between 1 and 65535"):
        # type: ignore # Invalid type (None)
        ProxyInfo(host="proxy.example.com", port=None)

    # Valid ports should not raise error
    try:
        ProxyInfo(host="proxy.example.com", port=1)
        ProxyInfo(host="proxy.example.com", port=65535)
        ProxyInfo(host="proxy.example.com", port=8080)
    except ValueError:
        pytest.fail("ValueError raised unexpectedly for valid port")

# pytest tests/domain/test_proxy_info.py を実行すると失敗する (Red)
