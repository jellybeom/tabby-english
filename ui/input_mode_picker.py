"""입력 모드 선택 화면 — 시나리오 결정 직후, 본격 대화 진입 전.

키보드(타이핑) 또는 음성(Web Speech API) 중 하나를 고르게 한다.
선택 결과는 그래프 State의 input_mode 필드에 저장되며 새로고침에도 유지된다.

음성 모드는 Chrome 또는 Edge에서 가장 안정적으로 동작한다.
"""

from typing import Optional

import streamlit as st


def render_input_mode_picker(scenario: str) -> Optional[str]:
    """입력 모드 선택 화면.

    Args:
        scenario: 사용자가 방금 선택한 시나리오 (표시용)

    Returns:
        "keyboard" 또는 "voice". 클릭이 없으면 None.
    """
    # 시나리오 카드와 동일한 비주얼 스타일 사용
    st.markdown(
        "<style>" + _CARD_CSS + "</style>",
        unsafe_allow_html=True,
    )

    # 컨텍스트 안내
    st.markdown(f"### `{scenario}` 시나리오를 선택하셨네요.")
    st.markdown("**어떻게 영어를 입력하시겠어요?**")
    st.caption("언제든 새 세션을 시작하면 다시 선택할 수 있어요.")
    st.write("")

    selected: Optional[str] = None

    # 카드 2개를 가로로 나란히 배치
    col_keyboard, col_voice = st.columns(2)

    with col_keyboard:
        st.markdown(
            "<div class='tabby-mode-card'>"
            "<div class='tabby-mode-emoji'>⌨️</div>"
            "<div class='tabby-mode-title'>키보드로 입력</div>"
            "<div class='tabby-mode-desc'>"
            "타이핑으로 영어 회화 연습.<br>"
            "막혔을 때 💡 버튼으로 추천을 받아요."
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        if st.button(
            "키보드로 시작",
            key="mode_keyboard",
            type="primary",
            use_container_width=True,
        ):
            selected = "keyboard"

    with col_voice:
        st.markdown(
            "<div class='tabby-mode-card tabby-mode-card-voice'>"
            "<div class='tabby-mode-emoji'>🎤</div>"
            "<div class='tabby-mode-title'>음성으로 말하기</div>"
            "<div class='tabby-mode-desc'>"
            "마이크로 영어를 말하고,<br>"
            "잠시 멈추면 다음 표현을 자동으로 띄워줘요."
            "<br><br><span style='font-size:11px; color:#888;'>"
            "Chrome 또는 Edge 권장"
            "</span>"
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        if st.button(
            "음성으로 시작",
            key="mode_voice",
            use_container_width=True,
        ):
            selected = "voice"

    return selected


# CSS는 별도 상수로 분리해 가독성 확보
_CARD_CSS = """
.tabby-mode-card {
  padding: 32px 20px 24px 20px;
  border-radius: 14px;
  background: linear-gradient(135deg, #f4f3fa 0%, #ece9f9 100%);
  text-align: center;
  margin-bottom: 8px;
  min-height: 200px;
}
.tabby-mode-card-voice {
  background: linear-gradient(135deg, #fdf6f0 0%, #fceedb 100%);
}
.tabby-mode-emoji {
  font-size: 48px;
  margin-bottom: 12px;
}
.tabby-mode-title {
  font-size: 17px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 10px;
}
.tabby-mode-desc {
  font-size: 13px;
  color: #555;
  line-height: 1.6;
}
"""
