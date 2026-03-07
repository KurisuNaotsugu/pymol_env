# scripts/pymol_fetch_af.py
from pymol import cmd
from pymol_topology.services.alphafold_db import AlphaFoldDBClient

# 実行関数の定義
def fetch_af(acc: str):
    cli = AlphaFoldDBClient()
    art = cli.fetch_structure(acc, prefer=("cif", "pdb"))
    print(f"[AF] saved: {art.local_path} (from {art.source_url})")
    cmd.load(str(art.local_path), f"AF_{art.accession}")
    cmd.zoom(f"AF_{art.accession}")

# pymolへのコマンド登録
cmd.extend("fetch_af", fetch_af)