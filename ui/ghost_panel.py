"""추천어 패널 — 입력창 바로 위에 칩(chip) 형태로 표시.

미완성 문장(partial)이 있으면 추천을 "이어 붙인 완성형"으로 보여주어,
사용자가 클릭 시 어떻게 합쳐지는지 한눈에 알 수 있게 한다.
"""

from typing import List, Optional

import streamlit as st


def render_ghost_panel(
    suggestions: List[str],
    partial: str = "",
) -> Optional[str]:
    """추천어 칩을 가로로 렌더링.

    Args:
        suggestions: LLM이 반환한 "이어 붙일 부분" 목록 (최대 3개)
        partial: 사용자가 현재 입력 중인 미완성 문장

    Returns:
        사용자가 선택한 최종 텍스트(미완성 + 추천이 합쳐진 형태). 없으면 None.
    """
    if not suggestions:
        return None

    label = "💡 다음 표현을 사용해보세요"
    if partial.strip():
        label = f'💡 "{partial.strip()}" 이어서 말하기'

    st.markdown(
        f"<div style='font-size:13px; color:#7c6ef2; margin-bottom:6px;'>{label}</div>",
        unsafe_allow_html=True,
    )

    clicked_full: Optional[str] = None
    cols = st.columns(len(suggestions))

    for idx, (col, suggestion) in enumerate(zip(cols, suggestions), start=1):
        # 미완성 + 추천을 결합한 최종 텍스트 (사용자가 보낼 실제 값)
        full_text = _join(partial, suggestion)

        with col:
            # 표시는 미완성 부분을 흐릿하게, 이어 붙는 부분을 진하게 보여줌
            display = _render_chip_label(partial, suggestion, number=idx)
            st.markdown(display, unsafe_allow_html=True)

            if st.button(
                "선택",
                key=f"ghost_chip_{idx}_{suggestion}",
                use_container_width=True,
            ):
                clicked_full = full_text

    return clicked_full


def _join(partial: str, suggestion: str) -> str:
    """미완성 문장과 추천을 자연스럽게 합친다.

    "I would like" + "to order a latte" → "I would like to order a latte"
    "I would like " + "to order a latte" → "I would like to order a latte"
    """
    partial = partial.rstrip()
    suggestion = suggestion.lstrip()
    if not partial:
        return suggestion
    return f"{partial} {suggestion}"


def _render_chip_label(partial: str, suggestion: str, number: int) -> str:
    """칩 위에 보여줄 HTML — 번호 배지 + 미완성(회색) + 추천(보라색)."""
    partial = partial.rstrip()
    suggestion = suggestion.lstrip()

    # 작은 원형 배지로 번호 표시
    badge = (
        f"<span style='display:inline-block; min-width:18px; height:18px; "
        f"border-radius:9px; background:#7c6ef2; color:white; "
        f"font-size:11px; font-weight:600; line-height:18px; "
        f"text-align:center; margin-right:6px;'>{number}</span>"
    )

    body = (
        f"<span style='color:#888;'>{partial} </span>"
        f"<span style='color:#7c6ef2; font-weight:600;'>{suggestion}</span>"
        if partial
        else f"<span style='color:#7c6ef2; font-weight:600;'>{suggestion}</span>"
    )

    return (
        "<div style='padding:8px 10px; border-radius:6px; "
        "background:#f4f3fa; text-align:center; "
        "font-size:14px; line-height:1.4; margin-bottom:4px;'>"
        f"{badge}{body}"
        "</div>"
    )
