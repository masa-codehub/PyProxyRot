# src/domain/proxy_info.py
from dataclasses import dataclass


@dataclass(frozen=True)
class ProxyInfo:
    """
    プロキシサーバーの接続情報を保持する不変の値オブジェクト。

    Attributes:
        host (str): プロキシサーバーのホスト名またはIPアドレス。空文字列は不可。
        port (int): プロキシサーバーのポート番号 (1-65535)。
    """
    host: str
    port: int

    def __post_init__(self):
        """初期化後のバリデーション"""
        # Host validation
        if not isinstance(self.host, str) or not self.host.strip():  # 空白のみも不可にする
            # Use ValueError for invalid values, TypeError might be for wrong type args
            raise ValueError("Host must be a non-empty string")

        # Port validation
        if not isinstance(self.port, int) or not (0 < self.port < 65536):
            raise ValueError("Port must be an integer between 1 and 65535")

# 必要に応じて src/domain/__init__.py を作成 (空ファイルでOK)
