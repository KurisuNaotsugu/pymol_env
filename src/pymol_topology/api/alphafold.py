# src/pymol_topology/api/alphafold.py
"""AlphaFold DB API クライアント（prediction エンドポイント）。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import requests

from pymol_topology.core.errors import FetchError, NotFoundError
from pymol_topology.core.http import make_session
from pymol_topology.core.models import ApiResponse


@dataclass
class AlphaFoldAPIConfig:
    api_base: str = "https://alphafold.ebi.ac.uk/api"
    timeout_sec: int = 60


class AlphaFoldAPI:
    """AlphaFold DB API の prediction エンドポイントを叩くクライアント。"""

    def __init__(
        self,
        config: AlphaFoldAPIConfig | None = None,
        session: requests.Session | None = None,
    ):
        self.config = config or AlphaFoldAPIConfig()
        self.session = session or make_session()

    def get_prediction_response(self, accession: str) -> ApiResponse:
        """Prediction API の生レスポンスを返す。4xx/5xx でも例外は上げない。"""
        acc = accession.strip()
        if not acc:
            raise FetchError("Empty accession")
        url = f"{self.config.api_base}/prediction/{acc}"
        r = self.session.get(url, timeout=self.config.timeout_sec)
        body: Any = None
        try:
            if r.text.strip():
                body = r.json()
        except Exception:
            pass
        headers = dict(r.headers) if r.headers else {}
        return ApiResponse(
            status_code=r.status_code,
            headers=headers,
            body=body,
            raw_text=r.text,
        )

    def get_prediction_metadata(self, accession: str) -> Any:
        """Prediction API のメタデータを返す。404/エラー時は例外。"""
        acc = accession.strip()
        if not acc:
            raise FetchError("Empty accession")
        url = f"{self.config.api_base}/prediction/{acc}"
        r = self.session.get(url, timeout=self.config.timeout_sec)
        if r.status_code == 404:
            raise NotFoundError(f"AlphaFold DB: accession not found: {acc}")
        if not r.ok:
            raise FetchError(f"AlphaFold DB API error {r.status_code}: {r.text[:200]}")
        return r.json()
