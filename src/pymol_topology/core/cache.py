# src/pymol_topology/core/cache.py
from __future__ import annotations
from pathlib import Path


def default_cache_dir(app_name: str = "pymol_topology") -> Path:
    """キャッシュディレクトリのデフォルトパスを取得

    Args:
        app_name(str): アプリケーション名

    Returns:
        Path(Path): キャッシュディレクトリのパス
    """
    base = Path.home() / ".cache" / app_name
    base.mkdir(parents=True, exist_ok=True)
    return base