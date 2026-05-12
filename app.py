"""Tabby English — Streamlit 진입점 (Phase 3 / Step 3).

Step 3 추가:
- 시나리오 카드 갤러리 (메인 영역)
- 채팅 풍선 미세 페이드인 애니메이션
- 피드백 결과를 탭/카드로 시각화 (세션 종료 후)
- 학습 이력 대시보드는 별도 페이지 (pages/)
"""

from __future__ import annotations

import os
import uuid
from typing import cast

import streamlit as st
from dotenv import load_dotenv

from src.graph import build_graph
from src.state import ConversationState
from ui import render_feedback, render_ghost_panel, render_scenario_picker

load_dotenv()

st.set_page_config(
    page_title="Tabby English",
    page_icon="🐱",
    layout="centered",
)


# ─── API 키 가드 ───
# 로컬 실행: .env 파일의 OPENAI_API_KEY를 읽음
# Streamlit Cloud: Secrets에 등록한 값이 환경변수처럼 자동 노출됨
if not os.getenv("OPENAI_API_KEY"):
    st.error(
        "⚠️ OpenAI API 키가 설정되지 않았습니다.\n\n"
        "**로컬 실행**: 프로젝트 루트에 `.env` 파일을 만들고 `OPENAI_API_KEY=sk-...`를 추가하세요.\n\n"
        '**Streamlit Cloud**: 앱 설정 → Secrets에 `OPENAI_API_KEY = "sk-..."`를 등록하세요.'
    )
    st.stop()


INPUT_KEY = "user_input_field"


@st.cache_resource
def get_app():
    return build_graph()


def make_initial_state(scenario: str) -> ConversationState:
    return {
        "scenario": scenario,
        "system_prompt": "",
        "raw_input": "",
        "partial_input": "",
        "input_signal": "utterance",
        "conversation_history": [],
        "last_ai_response": "",
        "ghost_suggestions": [],
        "feedback": {},
    }


# ─── 전역 스타일 ───
# 채팅 풍선 등장 시 미세한 페이드인 애니메이션
st.markdown(
    """
    <style>
      @keyframes tabby-fade-in {
        from { opacity: 0; transform: translateY(4px); }
        to   { opacity: 1; transform: translateY(0); }
      }
      div[data-testid="stChatMessage"] {
        animation: tabby-fade-in 0.35s ease-out;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# ─── 세션 영속성 ───
if "thread" in st.query_params:
    thread_id: str = st.query_params["thread"]
else:
    thread_id = f"web_{uuid.uuid4().hex[:8]}"
    st.query_params["thread"] = thread_id


# ─── 그래프 상태 조회 ───
app = get_app()
config = {"configurable": {"thread_id": thread_id}}
snapshot = app.get_state(config)
state_values = snapshot.values if snapshot.values else {}

current_scenario: str = state_values.get("scenario", "")
history: list = state_values.get("conversation_history", [])
suggestions: list[str] = state_values.get("ghost_suggestions", [])
feedback: dict = state_values.get("feedback", {})
session_started: bool = bool(current_scenario)
session_ended: bool = bool(feedback)


# ─── 사이드바 ───
with st.sidebar:
    st.markdown("### 🐱 Tabby English")
    st.caption("막힌 자리에 다음 표현을 띄워주는 영어 회화 코치")
    st.divider()

    if session_started:
        st.markdown(f"**시나리오**\n\n`{current_scenario}`")
        st.caption(f"세션 ID: `{thread_id}`")
        st.divider()

        if st.button("🔄 새 세션 시작", use_container_width=True):
            new_id = f"web_{uuid.uuid4().hex[:8]}"
            st.query_params["thread"] = new_id
            st.rerun()
    else:
        st.caption("왼쪽 위의 페이지 메뉴로 학습 이력도 확인할 수 있어요.")


# ─── 메인 영역 ───
if session_ended:
    # ───── 세션 종료: 피드백 화면 ─────
    st.markdown("# 🐱 Tabby English")
    st.success("세션이 종료되었습니다. 학습 결과를 확인해보세요.")
    st.divider()

    render_feedback(feedback)

    st.divider()
    if st.button("🔄 새 세션 시작하기", type="primary", use_container_width=True):
        new_id = f"web_{uuid.uuid4().hex[:8]}"
        st.query_params["thread"] = new_id
        st.rerun()

elif not session_started:
    # ───── 시작 전: 카드 갤러리 ─────
    st.markdown("# 🐱 Tabby English")
    st.markdown(
        "IDE의 자동완성처럼, 영어로 말하다 막히는 순간 다음 표현을 띄워주는 회화 코치."
    )
    st.write("")

    chosen = render_scenario_picker()
    if chosen:
        app.invoke(make_initial_state(chosen), config=config)
        st.rerun()

else:
    # ───── 대화 진행 ─────
    # 대화 이력
    for entry in history:
        role = "user" if entry["role"] == "user" else "assistant"
        avatar = "🧑" if role == "user" else "🤖"
        with st.chat_message(role, avatar=avatar):
            st.write(entry["text"])

    # 첫 사용자 안내
    if not history:
        st.info(
            "💡 막혔을 때는 옆 전구 버튼을 눌러보세요. 이어갈 표현을 추천해드려요.",
            icon="✨",
        )

    # 💡 버튼 펄스 강조 (추천이 비어있을 때만)
    if not suggestions:
        st.markdown(
            """
            <style>
              @keyframes tabby-pulse {
                0%, 100% { box-shadow: 0 0 0 0 rgba(124, 110, 242, 0.0); }
                50%      { box-shadow: 0 0 0 6px rgba(124, 110, 242, 0.25); }
              }
              div[data-testid="stForm"] div[data-testid="column"]:last-child button {
                animation: tabby-pulse 2.4s ease-in-out infinite;
              }
            </style>
            """,
            unsafe_allow_html=True,
        )

    # 위젯 그려지기 전 입력창 초기값 결정
    if "pending_chip" in st.session_state:
        st.session_state[INPUT_KEY] = st.session_state.pop("pending_chip")
    elif st.session_state.pop("clear_input_next", False):
        st.session_state[INPUT_KEY] = ""

    # 추천어 패널
    if suggestions:
        partial_for_preview = st.session_state.get("last_hint_partial", "")
        clicked = render_ghost_panel(suggestions, partial=partial_for_preview)
        if clicked:
            st.session_state["pending_chip"] = clicked
            st.rerun()

    # 입력 영역
    with st.form("input_form", clear_on_submit=False, border=False):
        col_input, col_send, col_hint = st.columns([6, 1, 1])

        with col_input:
            current_text = st.text_input(
                "입력",
                key=INPUT_KEY,
                label_visibility="collapsed",
                placeholder="영어로 말해보세요... ('end' 입력 시 세션 종료)",
            )
        with col_send:
            send_clicked = st.form_submit_button(
                "↑",
                use_container_width=True,
                type="primary",
                help="입력 전송 (Enter)",
            )
        with col_hint:
            hint_clicked = st.form_submit_button(
                "💡",
                use_container_width=True,
                help="현재 입력을 이어갈 표현 추천받기",
            )

    # 전송 처리
    if send_clicked and current_text.strip():
        with st.spinner("Partner가 응답 중..."):
            cast(
                ConversationState,
                app.invoke(
                    {"raw_input": current_text, "partial_input": ""},
                    config=config,
                ),
            )
        # 추천 관련 상태 정리
        app.update_state(config, {"ghost_suggestions": []})
        st.session_state.pop("last_hint_partial", None)
        st.session_state["clear_input_next"] = True
        st.rerun()

    elif hint_clicked:
        partial_to_send = current_text if current_text.strip() else ""
        st.session_state["last_hint_partial"] = partial_to_send
        with st.spinner("추천 표현 생성 중..."):
            cast(
                ConversationState,
                app.invoke(
                    {"raw_input": "", "partial_input": partial_to_send},
                    config=config,
                ),
            )
        st.rerun()
