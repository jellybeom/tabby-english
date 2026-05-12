"""Tabby English — Streamlit 진입점 (Phase 3 / Step 2).

핵심 동작:
- Enter 또는 ↑ 버튼으로 메시지 전송 (전송 후 입력창 자동 비움)
- 💡 버튼으로 추천어 요청 (입력창의 미완성 문장 유지)
- 추천 칩 클릭 시 합쳐진 텍스트가 입력창에 채워짐

Streamlit 위젯 생명주기 처리 패턴:
- 위젯이 그려진 후에는 session_state로 그 위젯 값을 수정할 수 없음.
- 그래서 "다음 실행 시 비우라"는 플래그를 남기고 st.rerun() 한다.
- 다음 실행에서 위젯이 그려지기 *전에* session_state를 정리.
"""

from __future__ import annotations

import uuid
from typing import cast

import streamlit as st
from dotenv import load_dotenv

from src.graph import build_graph
from src.state import ConversationState
from ui import render_ghost_panel

load_dotenv()

st.set_page_config(
    page_title="Tabby English",
    page_icon="🐱",
    layout="centered",
)


SCENARIO_PRESETS: dict[str, str] = {
    "☕ 카페에서 주문하기": "ordering at a cafe",
    "✈️ 공항에서 체크인": "checking in at the airport",
    "💼 면접 보기": "job interview at a tech company",
    "🛍️ 쇼핑하기": "shopping for clothes at a store",
    "🍽️ 식당 예약": "making a restaurant reservation",
}

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
session_started: bool = bool(current_scenario)


# ─── 사이드바 ───
with st.sidebar:
    st.markdown("### 🐱 Tabby English")
    st.caption("막힌 자리에 다음 표현을 띄워주는 영어 회화 코치")
    st.divider()

    if not session_started:
        st.markdown("**1. 시나리오 선택**")
        preset_label = st.selectbox(
            "프리셋",
            options=["직접 입력"] + list(SCENARIO_PRESETS.keys()),
            label_visibility="collapsed",
        )
        if preset_label == "직접 입력":
            scenario_input = st.text_input(
                "상황을 영어로 짧게 입력",
                placeholder="e.g., asking for directions",
            )
        else:
            scenario_input = SCENARIO_PRESETS[preset_label]
            st.caption(f"→ `{scenario_input}`")

        if st.button("대화 시작", type="primary", use_container_width=True):
            if scenario_input.strip():
                app.invoke(make_initial_state(scenario_input.strip()), config=config)
                st.rerun()
            else:
                st.warning("시나리오를 입력해주세요.")
    else:
        st.markdown(f"**시나리오**\n\n`{current_scenario}`")
        st.caption(f"세션 ID: `{thread_id}`")
        st.divider()
        if st.button("🔄 새 세션 시작", use_container_width=True):
            new_id = f"web_{uuid.uuid4().hex[:8]}"
            st.query_params["thread"] = new_id
            st.rerun()


# ─── 메인 영역 ───
if not session_started:
    st.markdown("# 🐱 Tabby English")
    st.markdown(
        "IDE의 자동완성처럼, 영어로 말하다 막히는 순간 다음 표현을 띄워주는 영어 회화 코치."
    )
    st.info("👈 왼쪽에서 시나리오를 선택하고 대화를 시작하세요.")
else:
    # 대화 이력
    for entry in history:
        role = "user" if entry["role"] == "user" else "assistant"
        avatar = "🧑" if role == "user" else "🤖"
        with st.chat_message(role, avatar=avatar):
            st.write(entry["text"])

    # ─── 위젯이 그려지기 전에 입력창 초기값 결정 ───
    # 우선순위: 칩 클릭 > 전송 직후 비우기 플래그
    if "pending_chip" in st.session_state:
        # 칩 클릭으로 채워야 할 텍스트 있음
        st.session_state[INPUT_KEY] = st.session_state.pop("pending_chip")
    elif st.session_state.pop("clear_input_next", False):
        # 직전 턴에 전송했음 → 비우기
        st.session_state[INPUT_KEY] = ""

    # ─── 추천어 패널 ───
    if suggestions:
        # 마지막 💡 요청 시점의 partial을 미리보기에 사용.
        # 정리(clear)는 새로운 💡 클릭 시점과 전송 시점에 명시적으로 한다.
        partial_for_preview = st.session_state.get("last_hint_partial", "")
        clicked = render_ghost_panel(suggestions, partial=partial_for_preview)
        if clicked:
            st.session_state["pending_chip"] = clicked
            st.rerun()

    # ─── 입력 영역 (form으로 Enter 전송 지원) ───
    # clear_on_submit=False: ↑는 비우고 💡는 안 비우도록 직접 제어한다.
    with st.form("input_form", clear_on_submit=False, border=False):
        col_input, col_send, col_hint = st.columns([6, 1, 1])

        with col_input:
            current_text = st.text_input(
                "입력",
                key=INPUT_KEY,
                label_visibility="collapsed",
                placeholder="영어로 말해보세요...",
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

    # ─── 전송 처리 ───
    if send_clicked and current_text.strip():
        with st.spinner("Partner가 응답 중..."):
            cast(
                ConversationState,
                app.invoke(
                    {"raw_input": current_text, "partial_input": ""},
                    config=config,
                ),
            )
        # 전송 후 추천 관련 상태를 모두 정리 → 다음 턴은 깨끗하게 시작
        app.update_state(config, {"ghost_suggestions": []})
        st.session_state.pop("last_hint_partial", None)
        # 다음 실행 시 입력창을 비우라는 플래그
        st.session_state["clear_input_next"] = True
        st.rerun()

    # ─── 추천 요청 처리 (입력창은 그대로 유지) ───
    elif hint_clicked:
        # current_text가 비어있으면 빈 문자열로 명시 전달 (이전 값 잔존 방지)
        partial_to_send = current_text if current_text.strip() else ""
        # UI 미리보기를 위해 이번 요청의 partial을 별도 저장
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
