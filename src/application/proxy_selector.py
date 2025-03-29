# src/application/proxy_selector.py
from typing import List

# --- 依存クラス/インターフェースを import ---
# これらが事前に定義されている必要があります
from src.domain.proxy_info import ProxyInfo
from src.application.proxy_provider import ProxyProvider

class ProxySelector:
    """
    ProxyProvider を通じて得られるプロキシリストから、
    指定されたインデックスに基づいてプロキシ情報を選択します。
    """
    def __init__(self, provider: ProxyProvider):
        """
        ProxySelector を初期化します。

        Args:
            provider: プロキシリストを提供する ProxyProvider のインスタンス。

        Raises:
            TypeError: provider 引数が ProxyProvider のインスタンスでない場合。
        """
        if not isinstance(provider, ProxyProvider):
            # コンストラクタでの型チェック
            raise TypeError("provider must be an instance of ProxyProvider")
        self._provider = provider

    def select_proxy(self, index: int) -> ProxyInfo:
        """
        指定されたインデックスに対応するプロキシ情報を取得します。

        Args:
            index: 取得したいプロキシのインデックス (0から始まる整数)。

        Returns:
            ProxyInfo: 選択されたプロキシ情報。

        Raises:
            TypeError: index 引数が整数でない場合。
            IndexError: プロキシリストが空の場合、または指定されたインデックスが
                        リストの有効範囲外の場合。
        """
        # インデックスの型チェック
        if not isinstance(index, int):
            raise TypeError("index must be an integer")

        # プロバイダーからプロキシリストを取得
        proxy_list = self._provider.get_proxies()

        # リストが空かチェック
        if not proxy_list:
            raise IndexError("Proxy list is empty")

        # インデックスが有効範囲内かチェック
        list_len = len(proxy_list)
        if 0 <= index < list_len:
            # 有効範囲内なら対応する ProxyInfo を返す
            return proxy_list[index]
        else:
            # 範囲外ならエラー
            raise IndexError(f"Proxy index out of range (index: {index}, size: {list_len})")

# 必要に応じて src/application/__init__.py (空ファイル) を作成してください。