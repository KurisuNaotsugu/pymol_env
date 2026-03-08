# src/pymol_topology/api/uniprot.py
"""UniProt REST API の汎用クライアント（配列・Subcellular Location・Feature 等）。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional

import requests

from pymol_topology.core.errors import FetchError, NotFoundError
from pymol_topology.core.http import make_session


@dataclass
class UniprotClientConfig:
    api_base: str = "https://rest.uniprot.org/uniprotkb"
    timeout_sec: int = 60


class UniprotClient:
    """UniProt REST API を叩く汎用クライアント。

    配列・Subcellular Location・Feature など、必要なフィールドを指定して取得する。
    """

    def __init__(
        self,
        config: UniprotClientConfig | None = None,
        session: requests.Session | None = None,
    ):
        self.config = config or UniprotClientConfig()
        self.session = session or make_session()

    def get_entry(self, accession: str, fields: Optional[List[str]] = None) -> dict[str, Any]:
        """指定アクセッションのエントリを取得する（任意フィールド指定）。

        Args:
            accession: UniProt accession
            fields: 取得するフィールド名のリスト。省略時は sequence のみ。

        Returns:
            エントリの辞書（results の先頭要素）
        """
        acc = accession.strip()
        if not acc:
            raise FetchError("Empty accession")
        url = f"{self.config.api_base}/search"
        params: dict[str, Any] = {
            "query": f"accession:{acc}",
            "format": "json",
        }
        if fields:
            params["fields"] = ",".join(fields)
        r = self.session.get(url, params=params, timeout=self.config.timeout_sec)
        if r.status_code == 404:
            raise NotFoundError(f"UniProt: accession not found: {acc}")
        if not r.ok:
            raise FetchError(f"UniProt API error {r.status_code}: {r.text[:200]}")
        data = r.json()
        results = data.get("results") or []
        if not results:
            raise NotFoundError(f"UniProt: no entry for accession: {acc}")
        return results[0]

    def get_sequence(self, accession: str) -> str:
        """アミノ酸配列を取得する。"""
        entry = self.get_entry(accession, fields=["sequence"])
        seq_obj = entry.get("sequence")
        if not seq_obj or "value" not in seq_obj:
            raise FetchError("UniProt API response missing sequence.value")
        return seq_obj["value"]

    def get_subcellular_location(self, accession: str) -> List[str]:
        """Subcellular Location（Feature 情報）を取得する。

        Returns:
            サブセルラー局在の文字列リスト（例: ["Cytoplasm", "Nucleus"]）
        """
        entry = self.get_entry(accession, fields=["comments"])
        comments = entry.get("comments") or []
        locations: List[str] = []
        for c in comments:
            ctype = c.get("commentType") or c.get("type")
            if ctype != "SUBCELLULAR_LOCATION":
                continue
            for loc in c.get("subcellularLocations") or []:
                loc_obj = loc.get("location") if isinstance(loc, dict) else None
                if loc_obj and "value" in loc_obj:
                    locations.append(loc_obj["value"])
        return locations

    def get_features(self, accession: str) -> List[dict[str, Any]]:
        """Feature 情報を取得する。

        Returns:
            Feature の辞書リスト（type, location, description 等）
        """
        entry = self.get_entry(accession, fields=["features"])
        return entry.get("features") or []
