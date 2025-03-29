# src/application/proxied_edge_browser.py

import logging
from typing import Optional, Type  # Type は __exit__ で使用
from types import TracebackType  # __exit__ の型ヒント用 (重複削除)
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.common.exceptions import WebDriverException

# 相対インポート
from ..adapters.edge_option_factory import EdgeOptionFactory
from ..application.proxy_selector import ProxySelector
from ..config.logging_config import get_logger
from ..domain.proxy_info import ProxyInfo  # 型ヒントで使用


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
        command_executor: str = 'http://selenium:4444/wd/hub',
        logger: logging.Logger | None = None
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
            raise TypeError(
                "proxy_selector must be an instance of ProxySelector")  # 英語に変更
        if not isinstance(option_factory, EdgeOptionFactory):
            raise TypeError(
                "option_factory must be an instance of EdgeOptionFactory")  # 英語に変更
        if not command_executor or not isinstance(command_executor, str):
            raise ValueError(
                "command_executor URL cannot be empty and must be a string")  # 英語に変更

        self._selector: ProxySelector = proxy_selector
        self._option_factory: EdgeOptionFactory = option_factory
        self._command_executor: str = command_executor
        self._logger: logging.Logger = logger or get_logger()
        self._driver: RemoteWebDriver | None = None

        self._logger.debug(
            # 英語に変更
            f"ProxiedEdgeBrowser initialized. Executor: {self._command_executor}")

    def start_browser(self, proxy_index: int) -> None:
        """
        指定されたインデックスのプロキシを使用して、Remote WebDriver経由で
        Edgeブラウザセッションを開始します。

        既にアクティブなセッションがある場合は、先にそれを閉じます。

        Args:
            proxy_index: ProxyProviderリストから使用するプロキシのインデックス。

        Raises:
            IndexError, TypeError: プロキシ選択またはオプション生成でのエラー。
            WebDriverException: WebDriverの起動に失敗した場合。
            Exception: その他の予期せぬエラー。
        """
        # ★ ログメッセージを英語に変更 ★
        self._logger.info(
            f"Attempting to start browser using proxy index {proxy_index}...")
        if self._driver is not None:
            self._logger.warning(
                "An active browser session exists. Closing it before starting a new one.")
            self.close_browser()

        try:
            # 1. プロキシを選択
            proxy_info: ProxyInfo = self._selector.select_proxy(proxy_index)
            self._logger.debug(
                f"Selected proxy: {proxy_info.host}:{proxy_info.port}")

            # 2. EdgeOptions を生成
            options: EdgeOptions = self._option_factory.create_options(
                proxy_info)
            try:
                args_str = " ".join(options.arguments) if hasattr(
                    options, 'arguments') and options.arguments else "N/A or Arguments not accessible"
                self._logger.debug(
                    f"Generated EdgeOptions with arguments: {args_str}")
            except Exception:
                self._logger.debug(
                    "Could not retrieve arguments from EdgeOptions (potentially changed in Selenium version).")

            # 3. Remote WebDriver セッションを開始
            self._logger.debug(
                f"Connecting to Remote WebDriver at {self._command_executor}...")
            self._driver = webdriver.Remote(
                command_executor=self._command_executor,
                options=options
            )
            session_id = getattr(self._driver, 'session_id', 'N/A')
            self._logger.info(
                f"Browser session started successfully. Session ID: {session_id}")

        except (IndexError, TypeError) as e:
            self._logger.error(
                f"Failed to prepare for browser start: {e}", exc_info=True)
            self._driver = None
            raise

        except WebDriverException as e:
            self._logger.error(
                f"Failed to start WebDriver session: {e}", exc_info=True)
            if self._driver:
                try:
                    self._driver.quit()
                except Exception:
                    pass
            self._driver = None
            raise

        except Exception as e:
            self._logger.error(
                f"An unexpected error occurred during browser startup: {e}", exc_info=True)
            if self._driver:
                try:
                    self._driver.quit()
                except Exception:
                    pass
            self._driver = None
            raise

    def take_screenshot(self, url: str, save_path: str) -> None:
        """(Issue #10 で実装)"""
        if self._driver is None:
            self._logger.error(
                "Browser not started when attempting to take screenshot.")  # 英語に変更
            raise RuntimeError(
                "Browser not started. Call start_browser() first.")  # 英語に変更

        self._logger.info(
            # 英語に変更
            f"Navigating to '{url}' and saving screenshot to '{save_path}'.")
        self._logger.warning(
            "take_screenshot is not implemented yet (Issue #10)")  # 英語に変更
        pass

    def close_browser(self) -> None:
        """
        現在アクティブなブラウザセッションを閉じ、WebDriverを終了します。
        """
        if self._driver is not None:
            self._logger.info("Closing browser session...")  # 英語に変更
            try:
                self._driver.quit()
                self._logger.info(
                    "Browser session closed successfully.")  # 英語に変更
            except Exception as e:
                self._logger.error(
                    # 英語に変更
                    f"Error occurred during browser quit: {e}", exc_info=True)
            finally:
                self._driver = None
        else:
            self._logger.debug("No active browser session to close.")  # 英語に変更
        # ★ 不要な pass を削除 ★

    # --- コンテキストマネージャサポート ---
    def __enter__(self) -> 'ProxiedEdgeBrowser':
        """'with' ステートメントで使用可能にします。self を返します。"""
        self._logger.debug("Entering ProxiedEdgeBrowser context.")  # 英語に変更
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None
    ) -> None:
        """'with' ブロック終了時にブラウザが確実に閉じられるようにします。"""
        self._logger.debug(
            "Exiting ProxiedEdgeBrowser context, ensuring browser closure.")  # 英語に変更
        self.close_browser()
