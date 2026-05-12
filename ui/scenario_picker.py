"""시나리오 선택 카드 갤러리 — 메인 화면의 첫 인상.

selectbox 대신 큰 카드 그리드로 시나리오를 보여줘, 첫 진입의 인상을 강화한다.
"직접 입력" 옵션은 갤러리 아래에 별도로 배치.
"""

from typing import Optional

import streamlit as st

# (이모지, 표시 이름, 영어 시나리오 문자열) 튜플
SCENARIO_CARDS: list[tuple[str, str, str]] = [
    ("☕", "카페 주문", "ordering at a cafe"),
    ("✈️", "공항 체크인", "checking in at the airport"),
    ("💼", "취업 면접", "job interview at a tech company"),
    ("🛍️", "쇼핑", "shopping for clothes at a store"),
    ("🍽️", "식당 예약", "making a restaurant reservation"),
    ("🚕", "택시 타기", "taking a taxi to the airport"),
]


def render_scenario_picker() -> Optional[str]:
    """카드 그리드를 그리고, 선택된 시나리오 문자열을 반환.

    Returns:
        클릭된 카드의 시나리오 문자열. 클릭이 없으면 None.
    """
    st.markdown(
        "<style>" + _CARD_CSS + "</style>",
        unsafe_allow_html=True,
    )

    st.markdown("### 어떤 상황을 연습해볼까요?")
    st.caption("아래 카드를 골라 바로 시작하거나, 맨 아래에서 직접 입력해보세요.")
    st.write("")

    selected: Optional[str] = None

    # 3열 그리드 (2줄에 걸쳐 6개 카드)
    rows_per_group = 3
    for row_start in range(0, len(SCENARIO_CARDS), rows_per_group):
        row = SCENARIO_CARDS[row_start : row_start + rows_per_group]
        cols = st.columns(rows_per_group)
        for col, (emoji, label, scenario) in zip(cols, row):
            with col:
                # 카드 모양의 비주얼만 markdown으로 그리고, 클릭은 그 아래 버튼이 담당.
                st.markdown(
                    f"<div class='tabby-card'>"
                    f"<div class='tabby-emoji'>{emoji}</div>"
                    f"<div class='tabby-label'>{label}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                if st.button(
                    "선택",
                    key=f"scenario_{scenario}",
                    use_container_width=True,
                ):
                    selected = scenario

    # 직접 입력 영역
    st.write("")
    with st.expander("✏️ 직접 시나리오 입력하기"):
        custom = st.text_input(
            "상황을 영어로 짧게 입력",
            placeholder="e.g., asking for directions in a foreign city",
            key="custom_scenario_input",
        )
        if st.button("이 상황으로 시작", type="primary", use_container_width=True):
            if custom.strip():
                selected = custom.strip()
            else:
                st.warning("시나리오를 입력해주세요.")

    return selected


_CARD_CSS = """
.tabby-card {
  padding: 28px 12px 18px 12px;
  border-radius: 14px;
  background: linear-gradient(135deg, #f4f3fa 0%, #ece9f9 100%);
  text-align: center;
  margin-bottom: 6px;
  transition: transform 0.2s ease;
}
.tabby-card:hover {
  transform: translateY(-2px);
}
.tabby-emoji {
  font-size: 38px;
  margin-bottom: 8px;
}
.tabby-label {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a2e;
}
"""
