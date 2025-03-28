# tests/config/test_logging_config.py
import pytest
import logging
import os
from pathlib import Path
import shutil
import time
import re # フォーマット確認用

# logging_config モジュール自体もインポートして _is_configured をリセット可能にする
import src.config.logging_config as logging_config
# ★ APP_LOGGER_NAME のインポートは削除し、必要な関数のみインポート
from src.config.logging_config import setup_logging, get_logger

# --- テスト用定数 ---
TEST_LOG_DIR_BASE = Path("./test_logs_output") # ベースディレクトリ
TEST_APP_LOGGER_NAME = 'test_logger' # ★ テスト用のロガー名を定義

@pytest.fixture
def test_log_paths(request):
    """テストごとにユニークなログパスを生成し、後始末するフィクスチャ"""
    test_name = request.node.name
    test_log_dir = TEST_LOG_DIR_BASE / test_name
    # test_app.log というファイル名は固定で良いでしょう
    test_log_file = test_log_dir / "test_app.log"

    # テスト実行前にディレクトリ削除 (存在すれば)
    if test_log_dir.exists():
        shutil.rmtree(test_log_dir)

    yield test_log_dir, test_log_file # パスをテスト関数に渡す

    # --- テスト実行後の後始末 ---
    logging_config._is_configured = False # 設定フラグをリセット
    logging.shutdown() # ハンドラを閉じる

    # 既存のハンドラをクリア (他のテストの影響を避けるため)
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    # ★ teardown でもテスト用ロガー名を使う
    app_logger = logging.getLogger(TEST_APP_LOGGER_NAME)
    for handler in app_logger.handlers[:]:
        app_logger.removeHandler(handler)
    app_logger.setLevel(logging.NOTSET) # レベルもリセット

    # テストログディレクトリを削除
    if test_log_dir.exists():
        time.sleep(0.1) # ファイルロック解除待ち
        try:
            shutil.rmtree(test_log_dir)
        except PermissionError as e:
             print(f"Warning: Could not remove {test_log_dir}: {e}")
        except Exception as e:
            print(f"Warning: Failed to remove test log dir: {e}")

# ★ 環境変数を設定する fixture を分離し、自動適用(autouse=True)
@pytest.fixture(autouse=True)
def auto_setup_env_vars(monkeypatch, test_log_paths):
    """各テストの前に自動で環境変数を設定するフィクスチャ"""
    test_log_dir, test_log_file = test_log_paths
    monkeypatch.setenv('LOG_DIR', str(test_log_dir))
    monkeypatch.setenv('LOG_FILE_NAME', test_log_file.name)
    monkeypatch.setenv('LOG_LEVEL', 'DEBUG') # デフォルトはDEBUGレベル
    monkeypatch.setenv('APP_LOGGER_NAME', TEST_APP_LOGGER_NAME) # ★ テスト用ロガー名を設定
    monkeypatch.delenv('LOG_FORMAT', raising=False) # デフォルトフォーマットを使用

# --- テスト関数 (monkeypatch引数を削除) ---

def test_setup_logging_creates_log_file(test_log_paths):
    """setup_logging() がログディレクトリを作成し、ログ出力でファイルが作られることを確認"""
    test_log_dir, test_log_file = test_log_paths

    # Act: INFOレベルでログを設定 (引数で上書き)
    setup_logging(log_level_override='INFO')
    logger = get_logger()
    logger.info("Initial log message to create file.")

    # Assert
    assert test_log_dir.is_dir()
    assert test_log_file.is_file()

def test_logging_output_format_and_level(test_log_paths):
    """設定したフォーマットとレベルでログが出力されることを確認 (DEBUGレベル)"""
    test_log_dir, test_log_file = test_log_paths
    # ★ 期待するパターンでテスト用ロガー名を使う
    expected_format_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - " + TEST_APP_LOGGER_NAME + r" - (DEBUG|INFO) - \[.+?:\d+\] - .+"

    # Act: setup_logging() は fixture により DEBUG レベルで設定される
    setup_logging()
    logger = get_logger()
    debug_msg = "Debug details"
    info_msg = "Information message"
    logger.debug(debug_msg)
    logger.info(info_msg)

    # Assert
    assert test_log_file.is_file()
    log_lines = test_log_file.read_text(encoding='utf-8').strip().splitlines()
    print(f"\nLog Content:\n{log_lines}") # デバッグ用出力

    # setup_logging 内の print はログファイルには記録されない
    # DEBUG と INFO のログが記録されているはず
    assert len(log_lines) >= 2
    if len(log_lines) >= 2:
        # フォーマットとメッセージの確認
        assert re.match(expected_format_pattern, log_lines[-2]) # DEBUG ログ
        assert f" - DEBUG - " in log_lines[-2]
        assert debug_msg in log_lines[-2]

        assert re.match(expected_format_pattern, log_lines[-1]) # INFO ログ
        assert f" - INFO - " in log_lines[-1]
        assert info_msg in log_lines[-1]

def test_log_level_filtering(test_log_paths, monkeypatch): # レベル変更するので monkeypatch は必要
    """設定したログレベルに応じてメッセージがフィルタリングされることを確認 (INFOレベル)"""
    test_log_dir, test_log_file = test_log_paths
    monkeypatch.setenv('LOG_LEVEL', 'INFO') # INFOレベルに上書き

    # Act
    setup_logging() # INFOレベルで設定される
    logger = get_logger()
    debug_msg = "This debug message should NOT be logged."
    info_msg = "This info message SHOULD be logged."
    logger.debug(debug_msg)
    logger.info(info_msg)

    # Assert
    assert test_log_file.is_file()
    log_content = test_log_file.read_text(encoding='utf-8')
    print(f"\nLog Content (INFO level):\n{log_content}") # デバッグ用出力

    assert debug_msg not in log_content # DEBUG は記録されない
    assert info_msg in log_content    # INFO は記録される

def test_get_logger_returns_configured_logger(test_log_paths, monkeypatch): # レベル変更するので monkeypatch は必要
    """get_logger() が設定済みのロガーインスタンスを返すことを確認"""
    test_log_dir, test_log_file = test_log_paths
    monkeypatch.setenv('LOG_LEVEL', 'ERROR') # ERRORレベルに上書き

    # Act
    setup_logging() # ERRORレベルで設定される
    # ★ get_logger() は環境変数からテスト用ロガー名を取得するはず
    logger1 = get_logger()
    # ★ テスト用ロガー名を明示的に指定しても同じインスタンスが返るはず
    logger2 = get_logger(TEST_APP_LOGGER_NAME)
    # ★ logging.getLogger でもテスト用ロガー名を使う
    logger_direct = logging.getLogger(TEST_APP_LOGGER_NAME)

    # Assert
    assert logger1 is logger2
    assert logger1 is logger_direct
    # ★ ロガー名のアサーションもテスト用ロガー名で行う
    assert logger1.name == TEST_APP_LOGGER_NAME
    # ★ レベルのアサーション (これが前回失敗していた箇所)
    assert logger1.level == logging.ERROR

def test_setup_logging_called_multiple_times(test_log_paths):
    """setup_logging() を複数回呼び出してもハンドラが重複しないことを確認"""
    test_log_dir, test_log_file = test_log_paths
    # setup_env_vars fixture により DEBUG レベル、テスト用ロガー名が設定される

    # Act
    setup_logging() # 1回目
    logger = get_logger()
    initial_handler_count = len(logger.handlers)
    assert initial_handler_count > 0 # ハンドラが設定されていることを確認
    logger.info("First log")

    setup_logging() # 2回目 (内部の _is_configured フラグでスキップされるはず)
    logger.info("Second log")

    # Assert
    assert len(logger.handlers) == initial_handler_count # ハンドラ数は増えない
    assert test_log_file.is_file()
    log_lines = test_log_file.read_text(encoding='utf-8').strip().splitlines()
    print(f"\nLog Content (Multiple calls):\n{log_lines}") # デバッグ用出力

    # ログファイルには logger.info の2行が記録されるはず
    assert len(log_lines) >= 2
    if len(log_lines) >= 2:
        assert "First log" in log_lines[-2]
        assert "Second log" in log_lines[-1]