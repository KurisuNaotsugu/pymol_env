#!/usr/bin/env python3
"""AlphaFold DB prediction API の生レスポンスをコマンドラインから閲覧するスクリプト。

使用例:
  python scripts/pymol_af_response.py P12345
  python scripts/pymol_af_response.py P12345 --body-only
  python scripts/pymol_af_response.py P12345 --raw
  python scripts/pymol_af_response.py P12345 --validate  # AF と UniProt の配列一致を検証
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# プロジェクトルートの src をパスに追加
_src = Path(__file__).resolve().parent.parent / "src"
if _src.exists():
    sys.path.insert(0, str(_src))

from pymol_topology.services.alphafold_db import AlphaFoldDBClient
from pymol_topology.services.sequence_validation import validate_sequence


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AlphaFold DB prediction API のレスポンスを取得して表示する",
    )
    parser.add_argument(
        "accession",
        type=str,
        help="UniProt accession（例: P12345）",
    )
    parser.add_argument(
        "--headers",
        action="store_true",
        help="ヘッダのみ表示",
    )
    parser.add_argument(
        "--body-only",
        action="store_true",
        help="パース済み body（JSON）のみ表示",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="生のレスポンス本文（raw_text）のみ表示",
    )
    parser.add_argument(
        "--no-indent",
        action="store_true",
        help="JSON を 1 行で表示（--body-only 時）",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="UniProt API の配列と AlphaFold の uniprotSequence が一致するか検証する",
    )
    args = parser.parse_args()

    if args.validate:
        result = validate_sequence(args.accession)
        print(result.message)
        if result.af_sequence is not None:
            head = result.af_sequence[:60]
            print(f"  AF (先頭60 aa):      {head}{'...' if len(result.af_sequence) > 60 else ''}")
        if result.uniprot_sequence:
            head = result.uniprot_sequence[:60]
            print(f"  UniProt (先頭60 aa): {head}{'...' if len(result.uniprot_sequence) > 60 else ''}")
        return 0 if result.match else 1

    client = AlphaFoldDBClient()
    try:
        resp = client.get_prediction_response(args.accession)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # 特定の表示モード
    if args.headers:
        print(f"status_code: {resp.status_code}")
        for k, v in resp.headers.items():
            print(f"  {k}: {v}")
        return 0
    if args.body_only:
        if resp.body is not None:
            indent = None if args.no_indent else 2
            print(json.dumps(resp.body, indent=indent, ensure_ascii=False))
        else:
            print(resp.raw_text)
        return 0
    if args.raw:
        print(resp.raw_text)
        return 0

    # デフォルト: 全体を表示
    print(f"status_code: {resp.status_code}")
    print("headers:")
    for k, v in resp.headers.items():
        print(f"  {k}: {v}")
    print("body:")
    if resp.body is not None:
        print(json.dumps(resp.body, indent=2, ensure_ascii=False))
    else:
        print(resp.raw_text[:1000] + ("..." if len(resp.raw_text) > 1000 else ""))

    return 0


if __name__ == "__main__":
    sys.exit(main())
