# src/pymol_topology/services/alphafold_db.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

import requests

from pymol_topology.api.alphafold import AlphaFoldAPI, AlphaFoldAPIConfig
from pymol_topology.core.cache import default_cache_dir
from pymol_topology.core.errors import FetchError
from pymol_topology.core.http import make_session
from pymol_topology.core.models import ApiResponse, StructureArtifact


@dataclass
class AlphaFoldDBConfig:
    # AlphaFold DB API（UniProt accession をキーにメタ情報を取得）
    # 文献/公開情報で紹介されている "prediction" endpoint。:contentReference[oaicite:2]{index=2}
    api_base: str = "https://alphafold.ebi.ac.uk/api"
    timeout_sec: int = 60
    cache_dir: Optional[Path] = None


class AlphaFoldDBClient:
    """AlphaFold DB から構造ファイルを取得するクラス
    - UniProt accession -> AlphaFold DB API を叩いてメタ情報取得
    - メタ情報からモデルファイルURL（mmCIF/PDB）を選択
    - ローカルへダウンロード（キャッシュ）

    Args:
        config(AlphaFoldDBConfig | None): 設定
        session(requests.Session | None): requests.Session インスタンス

    Returns:
        StructureArtifact(StructureArtifact): StructureArtifact インスタンス
    """

    def __init__(self, config: AlphaFoldDBConfig | None = None, session: requests.Session | None = None):
        self.config = config or AlphaFoldDBConfig()
        self.session = session or make_session()
        self.cache_dir = self.config.cache_dir or default_cache_dir()
        self._api = AlphaFoldAPI(
            config=AlphaFoldAPIConfig(
                api_base=self.config.api_base,
                timeout_sec=self.config.timeout_sec,
            ),
            session=self.session,
        )

    def fetch_structure(self, accession: str, prefer: Sequence[str] = ("cif", "pdb"), force: bool = False) -> StructureArtifact:
        """構造ファイルを取得

        Args:
            accession(str): UniProt accession
            prefer(Sequence[str]): 優先順位
            force(bool): 強制ダウンロードフラグ

        Returns:
            StructureArtifact(StructureArtifact): StructureArtifact インスタンス
        """
        acc = self._normalize_accession(accession) # UniProt accession を正規化

        meta = self._get_prediction_metadata(acc) # AlphaFold DB API を叩いてメタデータを取得
        url, fmt = self._pick_structure_url(meta, prefer=prefer) # メタ情報からモデルファイルURL（mmCIF/PDB）を選択

        local = self._local_path(acc, fmt) # ローカルパスを取得
        if local.exists() and not force:
            return StructureArtifact(accession=acc, format=fmt, local_path=local, source_url=url) # ローカルパスが存在し、強制ダウンロードフラグが立っていない場合は、ローカルパスを返す

        self._download(url, local) # ダウンロードを実行
        return StructureArtifact(accession=acc, format=fmt, local_path=local, source_url=url)

    def get_prediction_response(self, accession: str) -> ApiResponse:
        """AlphaFold DB prediction API の生レスポンスを取得（検証・デバッグ用）

        ステータスコードやヘッダ・本文をそのまま返す。4xx/5xx でも例外は上げず
        ApiResponse を返すので、呼び出し側でレスポンスを検証できる。

        Args:
            accession: UniProt accession

        Returns:
            ApiResponse: status_code, headers, body（パース済みJSON）, raw_text
        """
        acc = self._normalize_accession(accession)
        return self._api.get_prediction_response(acc)

    # -----------------------
    # internal
    # -----------------------
    def _normalize_accession(self, accession: str) -> str:
        """UniProt accession を正規化して返す

        Args:
            accession(str): UniProt accession

        Returns:
            str: 正規化されたUniProt accession
        """
        acc = accession.strip()
        if not acc:
            raise FetchError("Empty accession")
        return acc

    def _get_prediction_metadata(self, acc: str) -> Any:
        """AlphaFold DB API を叩いてメタデータを取得

        Args:
            acc(str): UniProt accession

        Raises:
            NotFoundError: UniProt accession が見つからない場合
            FetchError: AlphaFold DB API エラー

        Returns:
            Any: メタデータ

        """
        return self._api.get_prediction_metadata(acc)

    def _pick_structure_url(self, meta: Any, prefer: Sequence[str]) -> tuple[str, str]:
        """メタデータから構造ファイル用のURLを選択

        Args:
            meta(Any): メタデータ
            prefer(Sequence[str]): 優先順位

        Returns:
            tuple[str, str]: URLとファイル形式
        """
        obj = meta[0] if isinstance(meta, list) and meta else meta
        if not isinstance(obj, dict):
            raise FetchError("Unexpected metadata format from AlphaFold API")

        # URL候補収集（浅い + 深い探索）
        urls: list[str] = []
        for v in obj.values():
            if isinstance(v, str) and v.startswith("http"):
                urls.append(v)
        if not urls:
            urls = self._walk_for_urls(obj)

        # 構造っぽいものだけ
        struct_urls = [u for u in urls if any(x in u.lower() for x in (".cif", ".bcif", ".pdb"))]
        if not struct_urls:
            raise FetchError("Could not find any structure URLs in metadata (API may have changed)")

        def kind(u: str) -> str:
            ul = u.lower()
            if ".pdb" in ul:
                return "pdb"
            if ".bcif" in ul:
                return "bcif"
            if ".cif" in ul:
                return "cif"
            return "other"

        # prefer順を尊重しつつ、bcifは最後に回す
        preference = []
        for p in prefer:
            if p == "cif":
                preference.extend(["cif"])   # bcifはここに入れない
            elif p == "pdb":
                preference.extend(["pdb"])
            elif p == "bcif":
                preference.extend(["bcif"])
        # 何も指定がなければこの順
        if not preference:
            preference = ["cif", "pdb", "bcif"]

        # prefer順に最初に見つかったURLを採用
        for p in preference:
            for u in struct_urls:
                if kind(u) == p:
                    return u, p

        # 最後の保険
        u = struct_urls[0]
        return u, kind(u)

    def _walk_for_urls(self, d: Dict[str, Any]) -> list[str]:
        """ネストした dict/list を再帰的にたどり、構造ファイル用のURLを集めて返す

        Args:
            d(Dict[str, Any]): データ

        Returns:
            list[str]: URLリスト
        """
        found: list[str] = []
        stack: list[Any] = [d]
        while stack:
            cur = stack.pop()
            if isinstance(cur, dict):
                for v in cur.values():
                    stack.append(v)
            elif isinstance(cur, list):
                stack.extend(cur)
            elif isinstance(cur, str) and cur.startswith("http"):
                if any(x in cur.lower() for x in (".cif", ".bcif", ".pdb")):
                    found.append(cur)
        return found

    def _local_path(self, acc: str, fmt: str) -> Path:
        """ローカルパスを取得

        Args:
            acc(str): UniProt accession
            fmt(str): ファイル形式

        Returns:
            Path(Path): ローカルパス
        """
        sub = self.cache_dir / "alphafold"
        sub.mkdir(parents=True, exist_ok=True)
        ext = {"cif": "cif", "pdb": "pdb", "bcif": "bcif"}[fmt]
        return sub / f"AF_{acc}.{ext}"

    def _download(self, url: str, out_path: Path) -> None:
        """ダウンロードを実行

        Args:
            url(str): ソースURL
            out_path(Path): ローカルパス
        """
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with self.session.get(url, stream=True, timeout=self.config.timeout_sec) as r:
            if not r.ok:
                raise FetchError(f"Download failed {r.status_code}: {url}")
            tmp = out_path.with_suffix(out_path.suffix + ".part")
            with tmp.open("wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        f.write(chunk)
            tmp.replace(out_path)