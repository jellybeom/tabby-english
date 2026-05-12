"""Tabby English UI 컴포넌트.

각 모듈은 Streamlit 위젯 조합을 함수로 캡슐화한다.
app.py가 비대해지지 않도록 의도 단위로 분리.
"""

from ui.ghost_panel import render_ghost_panel

__all__ = ["render_ghost_panel"]
