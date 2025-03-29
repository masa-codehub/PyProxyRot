# src/application/proxied_edge_browser.py

import logging
from typing import Optional, Type
from types import TracebackType
from pathlib import Path  # ★ 追加: ディレクトリ操作のため
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.common.exceptions import WebDriverException

# 相対インポート
from ..adapters.edge_option_factory import EdgeOptionFactory
from ..application.proxy_selector import ProxySelector
from ..config.logging_config import get_logger
from ..domain.proxy_info import ProxyInfo


class ProxiedEdgeBrowser:
    """
    ProxyProviderから選択されたプロキシを使用し、Remote WebDriver経由で
    接続されるSelenium Edge WebDriverインスタンスを管理します。
    (以下、クラスDocstring省略)
    """

    def __init__(
        self,
        proxy_selector: ProxySelector,
        option_factory: EdgeOptionFactory,
        command_executor: str = 'http://selenium:4444/wd/hub',
        logger: logging.Logger | None = None
    ):
        """
        (コンストラクタDocstringと実装は変更なし)
        """
        if not isinstance(proxy_selector, ProxySelector):
            raise TypeError(
                "proxy_selector must be an instance of ProxySelector")
        if not isinstance(option_factory, EdgeOptionFactory):
            raise TypeError(
                "option_factory must be an instance of EdgeOptionFactory")
        if not command_executor or not isinstance(command_executor, str):
            raise ValueError(
                "command_executor URL cannot be empty and must be a string")

        self._selector: ProxySelector = proxy_selector
        self._option_factory: EdgeOptionFactory = option_factory
        self._command_executor: str = command_executor
        self._logger: logging.Logger = logger or get_logger()
        self._driver: RemoteWebDriver | None = None

        self._logger.debug(
            f"ProxiedEdgeBrowser initialized. Executor: {self._command_executor}")

    def start_browser(self, proxy_index: int) -> None:
        """
        (start_browser のDocstringと実装は変更なし - 英語ログ版)
        """
        self._logger.info(
            f"Attempting to start browser using proxy index {proxy_index}...")
        if self._driver is not None:
            self._logger.warning(
                "An active browser session exists. Closing it before starting a new one.")
            self.close_browser()

        try:
            proxy_info: ProxyInfo = self._selector.select_proxy(proxy_index)
            self._logger.debug(
                f"Selected proxy: {proxy_info.host}:{proxy_info.port}")
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

    # --- ↓↓↓ take_screenshot メソッドの修正 ↓↓↓ ---
    def take_screenshot(self, url: str, save_path_in_container: str) -> None:
        """
        現在のブラウザセッションで指定されたURLに移動し、スクリーンショットを保存します。
        保存先のディレクトリが存在しない場合は作成を試みます。

        Args:
            url: 移動先のURL。
            save_path_in_container: スクリーンショットを保存するフルファイルパス（コンテナ内のパス）。

        Raises:
            RuntimeError: ブラウザが起動していない場合。
            WebDriverException: URLへの移動またはスクリーンショットの保存に失敗した場合。
            OSError: スクリーンショット保存ディレクトリの作成に失敗した場合。
            Exception: その他の予期せぬエラー。
        """
        if self._driver is None:
            self._logger.error(
                "Browser not started when attempting to take screenshot.")
            raise RuntimeError(
                "Browser not started. Call start_browser() first.")

        self._logger.info(
            f"Navigating to '{url}' and saving screenshot to '{save_path_in_container}'.")
        try:
            # 1. 保存先ディレクトリの確認と作成
            save_dir = Path(save_path_in_container).parent
            if not save_dir.exists():
                self._logger.debug(
                    f"Creating screenshot directory: {save_dir}")
                # ★ mkdirのエラーはここで捕捉せず、外側のOSErrorで処理する方針に変更
                # (あるいは、ここでログを出力せずに raise する)
                save_dir.mkdir(parents=True, exist_ok=True)
                self._logger.debug(f"Directory {save_dir} ensured.")

            # 2. URLへ移動
            self._logger.debug(f"Navigating to URL: {url}")
            self._driver.get(url)
            self._logger.debug(f"Navigation to {url} completed.")

            # 3. スクリーンショットを保存
            self._logger.debug(
                f"Saving screenshot to: {save_path_in_container}")
            if not self._driver.save_screenshot(save_path_in_container):
                self._logger.warning(
                    f"save_screenshot returned False for path: {save_path_in_container}")
                # 必要ならここでエラーにする: raise IOError(...)
            self._logger.info(
                f"Screenshot saved successfully to '{save_path_in_container}'.")

        # ★★★ エラーハンドリングの修正: 具体的な例外を先に捕捉 ★★★
        except WebDriverException as e:
            # URL移動失敗やスクリーンショット保存失敗（WebDriver由来）
            self._logger.error(
                f"WebDriverException during screenshot process: {e}", exc_info=True)
            raise  # WebDriver関連のエラーは再送出
        except OSError as e:
            # ディレクトリ作成失敗 (mkdir が送出)
            self._logger.error(
                f"OSError during screenshot process (likely directory creation): {e}", exc_info=True)
            raise  # OSError も再送出
        except Exception as e:
            # その他の予期せぬエラー
            self._logger.error(
                f"An unexpected error occurred during screenshot process: {e}", exc_info=True)
            raise

    def close_browser(self) -> None:
        """
        現在アクティブなブラウザセッションを閉じ、WebDriverを終了します。
        """
        if self._driver is not None:
            self._logger.info("Closing browser session...")
            try:
                self._driver.quit()  # WebDriver セッションを終了し、ブラウザを閉じる
                self._logger.info("Browser session closed successfully.")
            except Exception as e:
                # quit() が失敗してもエラーログは出すが、例外は送出せず、後続処理を行う
                self._logger.error(
                    f"Error occurred during browser quit: {e}", exc_info=True)
            finally:
                # 成功・失敗に関わらず WebDriver インスタンスへの参照を解除
                self._driver = None
        else:
            self._logger.debug("No active browser session to close.")
        # pass # ← 不要なので削除

    def __enter__(self) -> 'ProxiedEdgeBrowser':
        """'with' ステートメントで使用可能にします。self を返します。"""
        self._logger.debug("Entering ProxiedEdgeBrowser context.")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None
    ) -> None:
        """'with' ブロック終了時にブラウザが確実に閉じられるようにします。"""
        self._logger.debug(
            "Exiting ProxiedEdgeBrowser context, ensuring browser closure.")
        self.close_browser()  # __exit__ で close_browser を呼び出す
