# src/pymol_topology/services/sequence_validation.py
"""AlphaFold DB の uniprotSequence と UniProt API の配列が一致するか検証する。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from pymol_topology.api.uniprot import UniprotClient
from pymol_topology.services.alphafold_db import AlphaFoldDBClient


def _normalize_sequence(s: str) -> str:
    """空白・改行を除き大文字に揃える。"""
    return "".join(s.split()).upper()


def _get_af_sequence_from_body(body: Any) -> Optional[str]:
    """AlphaFold API レスポンス body から配列を取得する。

    body は list の場合は先頭要素、dict の場合はそのまま。
    キーは "uniprotSequence" または "sequence"（API の将来変更に対応）。
    """
    if body is None:
        return None
    obj = body[0] if isinstance(body, list) and body else body
    if not isinstance(obj, dict):
        return None
    seq = obj.get("uniprotSequence") or obj.get("sequence")
    if isinstance(seq, str):
        return seq
    return None


@dataclass
class SequenceValidationResult:
    """配列一致検証の結果。"""
    match: bool
    af_sequence: Optional[str]
    uniprot_sequence: str
    message: str


def validate_sequence(accession: str) -> SequenceValidationResult:
    """AlphaFold API の uniprotSequence と UniProt API の配列が一致するか検証する。

    Args:
        accession: UniProt accession

    Returns:
        SequenceValidationResult: 一致可否・各配列・メッセージ
    """
    acc = accession.strip()
    client = AlphaFoldDBClient()
    resp = client.get_prediction_response(acc)

    if resp.status_code != 200:
        return SequenceValidationResult(
            match=False,
            af_sequence=None,
            uniprot_sequence="",
            message=f"AlphaFold API が 200 以外を返しました: {resp.status_code}",
        )

    af_seq = _get_af_sequence_from_body(resp.body)
    if af_seq is None:
        return SequenceValidationResult(
            match=False,
            af_sequence=None,
            uniprot_sequence="",
            message="AlphaFold レスポンスに uniprotSequence/sequence が見つかりません",
        )

    uniprot_client = UniprotClient(session=client.session)
    try:
        uniprot_seq = uniprot_client.get_sequence(acc)
    except Exception as e:
        return SequenceValidationResult(
            match=False,
            af_sequence=af_seq,
            uniprot_sequence="",
            message=f"UniProt API 取得失敗: {e}",
        )

    af_norm = _normalize_sequence(af_seq)
    up_norm = _normalize_sequence(uniprot_seq)
    match = af_norm == up_norm

    if match:
        msg = f"一致しました（長さ: {len(af_norm)} aa）"
    else:
        msg = f"不一致: AF長={len(af_norm)}, UniProt長={len(up_norm)}"

    return SequenceValidationResult(
        match=match,
        af_sequence=af_seq,
        uniprot_sequence=uniprot_seq,
        message=msg,
    )
