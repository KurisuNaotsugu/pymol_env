# src/pymol_topology/core/models.py
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


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