"""AFM (원자력현미경) 분야 dashboard — v0.7.0 P0-1, P0-2."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from metroai.content.domain_page import render_domain_page

st.set_page_config(
    page_title="AFM 분야 — MetroAI",
    page_icon="📐",
    layout="wide",
)

render_domain_page("afm")
