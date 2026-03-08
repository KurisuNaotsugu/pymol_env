# scripts/pymol_fetch_af.py
import sys
from pathlib import Path

from pymol import cmd

# プロジェクトルートの src をパスに追加（PyMOL 起動時用）
_src = Path(__file__).resolve().parent.parent / "src"
if _src.exists():
    sys.path.insert(0, str(_src))

from pymol_topology.services.alphafold_db import AlphaFoldDBClient
from pymol_topology.services.sequence_validation import validate_sequence


# 実行関数の定義
def fetch_af(acc: str):
    cli = AlphaFoldDBClient()
    art = cli.fetch_structure(acc, prefer=("cif", "pdb"))
    print(f"[AF] saved: {art.local_path} (from {art.source_url})")
    cmd.load(str(art.local_path), f"AF_{art.accession}")
    cmd.zoom(f"AF_{art.accession}")

    # UniProt 配列と AlphaFold uniprotSequence の一致を検証
    result = validate_sequence(art.accession)
    print(f"[AF] sequence validation: {result.message}")
    if not result.match and result.af_sequence and result.uniprot_sequence:
        print(f"  AF (先頭60 aa):      {result.af_sequence[:60]}{'...' if len(result.af_sequence) > 60 else ''}")
        print(f"  UniProt (先頭60 aa): {result.uniprot_sequence[:60]}{'...' if len(result.uniprot_sequence) > 60 else ''}")


# pymolへのコマンド登録
cmd.extend("fetch_af", fetch_af)