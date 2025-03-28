# src/config/logging_config.py
import logging
import logging.config
import os
from pathlib import Path
from typing import Optional
import sys # 標準エラー出力用にインポート

# --- デフォルト値のみモジュールレベルで定義 ---
DEFAULT_LOG_DIR = Path("/app")
DEFAULT_LOG_FILE_NAME = "app.log"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
DEFAULT_APP_LOGGER_NAME = 'my_cool_app' # ★ デフォルトのロガー名

_is_configured = False

def setup_logging(log_level_override: Optional[str] = None):
    """
    アプリケーションの基本的なファイルロギングを設定する。
    環境変数 LOG_LEVEL、LOG_DIR、LOG_FILE_NAME、LOG_FORMAT を参照する。
    複数回呼び出されても設定が重複しないようにする。
    ハンドラチェックの条件式を修正。デバッグプリント付き。

    Args:
        log_level_override: 環境変数の代わりに指定するログレベル (例: 'DEBUG')。
    """
    global _is_configured
    print("\nDEBUG: --- setup_logging called ---") # ★ 関数呼び出し確認
    if _is_configured:
        print("DEBUG: Logging already configured, skipping.") # ★ スキップ確認
        return

    # --- 環境変数の読み込み ---
    log_dir_str = os.getenv('LOG_DIR', str(DEFAULT_LOG_DIR))
    log_file_name = os.getenv('LOG_FILE_NAME', DEFAULT_LOG_FILE_NAME)
    level_str_env = os.getenv('LOG_LEVEL', DEFAULT_LOG_LEVEL)
    level_str = (log_level_override or level_str_env).upper()
    log_format = os.getenv('LOG_FORMAT', DEFAULT_LOG_FORMAT)
    app_logger_name = os.getenv('APP_LOGGER_NAME', DEFAULT_APP_LOGGER_NAME)
    print(f"DEBUG: Read config - log_dir='{log_dir_str}', file='{log_file_name}', level='{level_str}', logger='{app_logger_name}'") # ★ 読み込み値確認

    log_dir = Path(log_dir_str)
    log_file_path = log_dir / log_file_name
    log_level = getattr(logging, level_str, logging.INFO)

    # --- ディレクトリ作成処理 ---
    try:
        print(f"DEBUG: Attempting to create directory {log_dir}") # ★ ディレクトリ作成試行確認
        log_dir.mkdir(parents=True, exist_ok=True)
        print(f"DEBUG: Directory {log_dir} ensured.") # ★ ディレクトリ作成/存在確認
    except OSError as e:
        print(f"ERROR: Failed to create log directory {log_dir}: {e}", file=sys.stderr)
        print("DEBUG: Exiting setup_logging due to directory creation error.") # ★ 早期リターン確認
        return # ディレクトリ作成失敗時は設定中断

    logger = logging.getLogger(app_logger_name)
    logger.setLevel(log_level)
    print(f"DEBUG: Logger '{logger.name}' level set to {log_level} ({logging.getLevelName(log_level)})") # ★ ロガーレベル設定確認

    # --- ★★★ ハンドラ重複チェックの条件式を変更 ★★★ ---
    print(f"DEBUG: Checking handlers for logger '{logger.name}'. Current count: {len(logger.handlers)}") # ★ ハンドラ数確認
    if not logger.handlers:      # ★ 修正: リストが空かどうかで直接チェック
        print("DEBUG: No handlers found, proceeding to add new ones.") # ★ ハンドラ追加ブロック実行確認
        formatter = logging.Formatter(log_format)
        file_handler_added = False
        try:
            print(f"DEBUG: Attempting to create FileHandler for {log_file_path}") # ★ ファイルハンドラ作成試行確認
            file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
            file_handler.setLevel(log_level) # ハンドラレベルも設定
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            file_handler_added = True
            print("DEBUG: FileHandler added successfully.") # ★ ファイルハンドラ追加成功確認
        except OSError as e:
             # エラーは標準エラーに出力する
             print(f"ERROR: Failed to create file handler for {log_file_path}: {e}", file=sys.stderr)
             print("DEBUG: FileHandler creation failed, continuing to add ConsoleHandler.") # ★ ファイルハンドラ失敗確認

        # コンソールハンドラも追加
        print("DEBUG: Attempting to create StreamHandler (Console)") # ★ コンソールハンドラ作成試行確認
        console_handler = logging.StreamHandler(sys.stdout) # 標準出力へ
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        print("DEBUG: StreamHandler added successfully.") # ★ コンソールハンドラ追加成功確認

        # 設定完了メッセージ
        log_destination = f"file={log_file_path}" if file_handler_added else "console only"
        # logger.info を使用
        logger.info(f"Logging configured: level={level_str}, {log_destination}")
        print(f"DEBUG: Configuration log message sent via logger.") # ★ logger.info を呼んだことを確認

    else:
        # この else ブロックは、初回呼び出しでは実行されないはず
        print(f"DEBUG: Logger '{logger.name}' already has handlers ({len(logger.handlers)} found), not adding duplicates.") # ★ ハンドラ重複防止確認

    _is_configured = True
    print("DEBUG: --- setup_logging finished ---") # ★ 関数終了確認

# get_logger 関数は変更なし
def get_logger(name: Optional[str] = None) -> logging.Logger:
    logger_name = name or os.getenv('APP_LOGGER_NAME', DEFAULT_APP_LOGGER_NAME)
    return logging.getLogger(logger_name)