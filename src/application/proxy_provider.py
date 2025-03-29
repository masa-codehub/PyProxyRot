# src/application/proxy_provider.py
from abc import ABC, abstractmethod
from typing import List

# 依存する ProxyInfo をインポート
# このimportが成功するためには src/domain/proxy_info.py が必要です。
from src.domain.proxy_info import ProxyInfo

class ProxyProvider(ABC):
    """
    プロキシ情報のリストを提供するインターフェース (Abstract Base Class)。
    サブクラスは get_proxies メソッドを実装する必要があります。
    """
    @abstractmethod
    def get_proxies(self) -> List[ProxyInfo]:
        """
        利用可能なプロキシ情報のリストを取得する。

        Returns:
            List[ProxyInfo]: プロキシ情報のリスト。リストが空の場合もあります。
        """
        pass # 実装はサブクラスに委ねる

class ListProxyProvider(ProxyProvider):
    """
    メモリ上のPythonリストからプロキシ情報を提供する ProxyProvider の具象クラス。
    """
    def __init__(self, proxy_list: List[ProxyInfo]):
        """
        ListProxyProviderを初期化する。

        Args:
            proxy_list: 提供するプロキシ情報のリスト。

        Raises:
            TypeError: proxy_listがリストでない場合、またはリスト内の要素が ProxyInfo インスタンスでない場合。
        """
        # 入力値の型チェック
        if not isinstance(proxy_list, list):
            raise TypeError("proxy_list must be a list")
        if not all(isinstance(item, ProxyInfo) for item in proxy_list):
            raise TypeError("All items in proxy_list must be ProxyInfo instances")

        # リストを内部属性として保持
        self._proxy_list = proxy_list

    def get_proxies(self) -> List[ProxyInfo]:
        """
        初期化時に渡されたプロキシ情報のリストを返す。

        Returns:
            List[ProxyInfo]: プロキシ情報のリスト。
        """
        # 内部で保持しているリストの参照をそのまま返す
        return self._proxy_list

# 必要に応じて src/application/__init__.py (空ファイル) を作成してください。