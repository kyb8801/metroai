"""SEM (주사전자현미경) 분야 dashboard — v0.7.0 P0-1, P0-2.

분야 진입 wizard 의 SEM 카드 클릭 시 도착하는 페이지.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from metroai.content.domain_page import render_domain_page

st.set_page_config(
    page_title="SEM 분야 — MetroAI",
    page_icon="🔬",
    layout="wide",
)

render_domain_page("sem")
