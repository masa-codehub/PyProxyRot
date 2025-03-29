# src/application/proxied_edge_browser.py

import logging
from typing import Optional, Type  # Typeを使うために追加
from types import TracebackType  # Typeを使うために追加
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver  # 型ヒントのため
from selenium.webdriver.edge.options import Options as EdgeOptions  # 型ヒントのため

# アプリケーション層内やアダプター層の依存を相対インポート
from ..adapters.edge_option_factory import EdgeOptionFactory
from ..application.proxy_selector import ProxySelector
from ..config.logging_config import get_logger  # 設定済みのロガーを使用


class ProxiedEdgeBrowser:
    """
    ProxyProviderから選択されたプロキシを使用し、Remote WebDriver経由で
    接続されるSelenium Edge WebDriverインスタンスを管理します。

    ブラウザの起動（プロキシ使用）、スクリーンショット取得、終了処理を扱います。
    コンテキストマネージャとしても利用可能です。
    """

    def __init__(
        self,
        proxy_selector: ProxySelector,
        option_factory: EdgeOptionFactory,
        command_executor: str = 'http://selenium:4444/wd/hub',  # Selenium HubのデフォルトURL
        logger: Optional[logging.Logger] = None
    ):
        """
        ProxiedEdgeBrowserを初期化します。

        Args:
            proxy_selector: プロキシを選択するための ProxySelector インスタンス。
            option_factory: EdgeOptions を作成するための EdgeOptionFactory インスタンス。
            command_executor: Remote WebDriverサーバー (Selenium Hub/Standalone) のURL。
            logger: オプションのロガーインスタンス。Noneの場合はデフォルトのロガーを使用します。

        Raises:
            TypeError: proxy_selector または option_factory の型が不正な場合。
            ValueError: command_executor が空または文字列でない場合。
        """
        if not isinstance(proxy_selector, ProxySelector):
            raise TypeError("proxy_selector は ProxySelector のインスタンスである必要があります")
        if not isinstance(option_factory, EdgeOptionFactory):
            raise TypeError(
                "option_factory は EdgeOptionFactory のインスタンスである必要があります")
        if not command_executor or not isinstance(command_executor, str):
            raise ValueError("command_executor URL は空にできず、文字列である必要があります")

        self._selector: ProxySelector = proxy_selector
        self._option_factory: EdgeOptionFactory = option_factory
        self._command_executor: str = command_executor
        self._logger: logging.Logger = logger or get_logger()  # 指定がない場合はデフォルトロガーを取得
        # WebDriverインスタンス、初期値はNone
        self._driver: Optional[RemoteWebDriver] = None

        self._logger.debug(
            f"ProxiedEdgeBrowser が初期化されました。Executor: {self._command_executor}")

    def start_browser(self, proxy_index: int) -> None:
        """
        指定されたインデックスのプロキシを使用して、Remote WebDriver経由で
        Edgeブラウザセッションを開始します。

        既にアクティブなセッションがある場合は、先にそれを閉じます。

        Args:
            proxy_index: ProxyProviderリストから使用するプロキシのインデックス。

        Raises:
            IndexError: proxy_index が不正な場合。
            WebDriverException: WebDriverの起動に失敗した場合。
            # オプション生成やプロキシ選択中に他の例外が発生する可能性あり
        """
        self._logger.info(f"プロキシインデックス {proxy_index} を使用してブラウザを起動します...")
        # 既存セッションがあれば閉じる
        self.close_browser()

        # --- 実際の処理は Issue #9 で実装 ---
        self._logger.warning("start_browser の実装はまだです (Issue #9)")  # 実装待ちを示すログ
        pass  # 実装待ちのプレースホルダー
        # 将来の実装例:
        # try:
        #     proxy_info = self._selector.select_proxy(proxy_index)
        #     self._logger.debug(f"選択されたプロキシ: {proxy_info.host}:{proxy_info.port}")
        #     options = self._option_factory.create_options(proxy_info)
        #     self._logger.debug("EdgeOptions を生成しました。")
        #     self._driver = webdriver.Remote(command_executor=self._command_executor, options=options)
        #     self._logger.info("ブラウザセッションが正常に開始されました。")
        # except IndexError as e:
        #     self._logger.error(f"無効なプロキシインデックス: {proxy_index} - {e}")
        #     raise # エラーを再送出
        # except Exception as e:
        #     self._logger.error(f"ブラウザ起動中にエラーが発生しました: {e}", exc_info=True)
        #     raise # エラーを再送出

    def take_screenshot(self, url: str, save_path: str) -> None:
        """
        現在のブラウザセッションで指定されたURLに移動し、スクリーンショットを保存します。

        Args:
            url: 移動先のURL。
            save_path: スクリーンショットを保存するフルファイルパス。

        Raises:
            RuntimeError: ブラウザが起動していない場合。
            WebDriverException: URLへの移動またはスクリーンショットの保存に失敗した場合。
        """
        if self._driver is None:
            self._logger.error("スクリーンショット取得試行時、ブラウザが起動していません。")
            raise RuntimeError("ブラウザが起動していません。先に start_browser() を呼び出してください。")

        self._logger.info(f"URL '{url}' に移動し、スクリーンショットを '{save_path}' に保存します。")
        # --- 実際の処理は Issue #10 で実装 ---
        self._logger.warning("take_screenshot の実装はまだです (Issue #10)")
        pass  # 実装待ちのプレースホルダー
        # 将来の実装例:
        # try:
        #     self._driver.get(url)
        #     self._logger.debug(f"URL '{url}' に移動しました。")
        #     self._driver.save_screenshot(save_path)
        #     self._logger.info(f"スクリーンショットを '{save_path}' に保存しました。")
        # except Exception as e:
        #     self._logger.error(f"スクリーンショット取得中にエラーが発生しました: {e}", exc_info=True)
        #     raise

    def close_browser(self) -> None:
        """
        現在アクティブなブラウザセッションを閉じ、WebDriverを終了します。
        """
        if self._driver is not None:
            self._logger.info("ブラウザセッションを閉じます...")
            try:
                self._driver.quit()
                self._logger.info("ブラウザセッションを正常に閉じました。")
            except Exception as e:
                # quit() が失敗してもエラーログは出すが、処理は続行する（リソース解放を試みる）
                self._logger.error(f"ブラウザ終了処理中にエラーが発生しました: {e}", exc_info=True)
            finally:
                self._driver = None  # WebDriverインスタンスへの参照を解除
        else:
            self._logger.debug("閉じるべきアクティブなブラウザセッションはありません。")
        # --- 実装の改善は Issue #11 で ---
        pass  # 実装待ちのプレースホルダー

    # --- コンテキストマネージャサポート ---
    def __enter__(self) -> 'ProxiedEdgeBrowser':
        """'with' ステートメントで使用可能にします。self を返します。"""
        # 注意: enter 時にブラウザは自動起動しません。
        # 'with' ブロック内で明示的に start_browser() を呼び出す必要があります。
        self._logger.debug("ProxiedEdgeBrowser コンテキストに入ります。")
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> None:
        """'with' ブロック終了時にブラウザが確実に閉じられるようにします。"""
        self._logger.debug("ProxiedEdgeBrowser コンテキストを抜けます。ブラウザ終了処理を実行します。")
        self.close_browser()
