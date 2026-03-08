# src/pymol_topology/core/models.py
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass(frozen=True)
class ApiResponse:
    """API の生レスポンス（検証・デバッグ用）

    Args:
        status_code: HTTP ステータスコード
        headers: レスポンスヘッダ（キーは文字列）
        body: パース済み JSON（パース失敗時は None）
        raw_text: 生のレスポンス本文
    """
    status_code: int
    headers: dict[str, str]
    body: Any
    raw_text: str


@dataclass(frozen=True)
class StructureArtifact:
    """AlphaFold DB から取得した構造ファイルのメタ情報

    Args:
        accession(str): UniProt accession
        format(str): ファイル形式
        local_path(Path): ローカルパス
        source_url(str): ソースURL
        checksum(Optional[str]): チェックサム
    """
    accession: str
    format: str
    local_path: Path
    source_url: str
    checksum: Optional[str] = None 