# src/application/proxy_provider.py
from abc import ABC, abstractmethod
from typing import List

# 依存する ProxyInfo をインポート
from src.domain.proxy_info import ProxyInfo


class ProxyProvider(ABC):
    """
    プロキシ情報のリストを提供するインターフェース (Abstract Base Class)。
    """
    @abstractmethod
    def get_proxies(self) -> List[ProxyInfo]:
        """
        利用可能なプロキシ情報のリストを取得する。

        Returns:
            List[ProxyInfo]: プロキシ情報のリスト。
        """
        pass  # 実装はサブクラスで行う


class ListProxyProvider(ProxyProvider):
    """
    メモリ上のリストからプロキシ情報を提供する ProxyProvider の具象クラス。
    """

    def __init__(self, proxy_list: List[ProxyInfo]):
        """
        ListProxyProviderを初期化する。

        Args:
            proxy_list: 提供するプロキシ情報のリスト。

        Raises:
            TypeError: proxy_listがリストでない場合、またはリスト内の要素が ProxyInfo インスタンスでない場合。
        """
        if not isinstance(proxy_list, list):
            raise TypeError("proxy_list must be a list")
        if not all(isinstance(item, ProxyInfo) for item in proxy_list):
            raise TypeError(
                "All items in proxy_list must be ProxyInfo instances")

        # リストを内部に保持
        self._proxy_list = proxy_list

    def get_proxies(self) -> List[ProxyInfo]:
        """
        初期化時に渡されたプロキシ情報のリストを返す。

        Returns:
            List[ProxyInfo]: プロキシ情報のリスト。
        """
        # リスト自体を返す（変更されるリスクを受け入れる場合）
        # 安全性を高めるなら self._proxy_list.copy() を返す
        return self._proxy_list

# 必要に応じて __init__.py ファイルを作成
# src/application/__init__.py (空ファイルでOK)
# src/__init__.py (空ファイルでOK)
