# src/adapters/edge_option_factory.py
from selenium.webdriver.edge.options import Options as EdgeOptions # Seleniumからインポート

# 依存クラスを import
# このimportが成功するためには src/domain/proxy_info.py が必要です。
from src.domain.proxy_info import ProxyInfo

class EdgeOptionFactory:
    """
    ProxyInfo データを受け取り、プロキシサーバー設定を含む
    Selenium WebDriver の EdgeOptions オブジェクトを生成するファクトリクラス。
    """
    def create_options(self, proxy_info: ProxyInfo) -> EdgeOptions:
        """
        指定されたプロキシ情報に基づいて EdgeOptions インスタンスを生成し、
        プロキシサーバーを設定します。

        Args:
            proxy_info: 設定に使用するプロキシサーバーの情報 (ProxyInfoオブジェクト)。

        Returns:
            EdgeOptions: プロキシ設定が追加された EdgeOptions インスタンス。

        Raises:
            TypeError: proxy_info 引数が ProxyInfo のインスタンスでない場合。
        """
        # 入力オブジェクトの型を検証
        if not isinstance(proxy_info, ProxyInfo):
            raise TypeError("proxy_info must be an instance of ProxyInfo")

        # 新しい EdgeOptions インスタンスを作成
        options = EdgeOptions()

        # プロキシ設定用の引数文字列を作成
        proxy_argument = f"--proxy-server={proxy_info.host}:{proxy_info.port}"

        # 作成した引数を EdgeOptions に追加
        options.add_argument(proxy_argument)
        # ★★★ 証明書エラーを無視するオプションを追加 ★★★
        options.add_argument("--ignore-certificate-errors")

        # 必要に応じて、他のデフォルトオプションをここに追加できます
        # 例: ヘッドレスモード
        # options.add_argument("--headless")
        # options.add_argument("--disable-gpu") # ヘッドレスモードで推奨される場合がある

        # 設定済みの options オブジェクトを返す
        return options

# 必要に応じて src/adapters/__init__.py (空ファイル) を作成してください。