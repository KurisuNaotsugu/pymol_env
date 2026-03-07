# src/pymol_topology/core/http.py
from __future__ import annotations
import requests


def make_session(user_agent: str = "pymol-topology-plugin/0.1") -> requests.Session:
    """ヘッダー情報を設定したrequests.Session を作成

    Args:
        user_agent(str): ユーザーエージェント

    Returns:
        requests.Session(requests.Session): requests.Session インスタンス
    """
    s = requests.Session()
    s.headers.update({
        "User-Agent": user_agent,
        "Accept": "application/json",
    })
    return s