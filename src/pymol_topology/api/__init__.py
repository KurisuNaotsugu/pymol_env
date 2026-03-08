# src/pymol_topology/api/__init__.py
"""外部 API クライアント（AlphaFold DB, UniProt 等）。"""
from pymol_topology.api.alphafold import AlphaFoldAPI, AlphaFoldAPIConfig
from pymol_topology.api.uniprot import UniprotClient, UniprotClientConfig

__all__ = [
    "AlphaFoldAPI",
    "AlphaFoldAPIConfig",
    "UniprotClient",
    "UniprotClientConfig",
]
