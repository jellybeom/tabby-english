"""Tabby English — Streamlit 진입점.

화면 흐름:
1. 시나리오 미선택  → 카드 갤러리
2. 모드 미선택      → 입력 모드 선택 (keyboard / voice)
3. 대화 진행        → 모드에 따라 다른 입력 UI
4. 'end' 입력       → 학습 피드백 화면
"""

from __future__ import annotations

import os
import uuid
from typing import cast

import streamlit as st
from dotenv import load_dotenv

from components.ghost_input import ghost_input
from src.graph import build_graph
from src.state import ConversationState, InputMode
from ui import (
    render_feedback,
    render_ghost_panel,
    render_input_mode_picker,
    render_scenario_picker,
)

load_dotenv()

st.set_page_config(
    page_title="Tabby English",
    page_icon="🐱",
    layout="centered",
)


# ─── API 키 가드 ───
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
    """시나리오 선택 직후의 초기 State.

    input_mode는 다음 화면(모드 선택)에서 별도 update_state로 채운다.
    """
    return {
        "scenario": scenario,
        "system_prompt": "",
        "input_mode": cast(InputMode, ""),  # 의도적으로 빈 값
        "raw_input": "",
        "partial_input": "",
        "input_signal": "utterance",
        "conversation_history": [],
        "last_ai_response": "",
        "ghost_suggestions": [],
        "feedback": {},
    }


# ─── 전역 스타일 (채팅 풍선 페이드인) ───
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


# ─── 세션 영속성 (URL의 thread 파라미터로 동일 세션 유지) ───
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
current_mode: str = state_values.get("input_mode", "")
history: list = state_values.get("conversation_history", [])
suggestions: list[str] = state_values.get("ghost_suggestions", [])
feedback: dict = state_values.get("feedback", {})

scenario_chosen: bool = bool(current_scenario)
mode_chosen: bool = bool(current_mode)
session_ended: bool = bool(feedback)


# ─── 사이드바 ───
with st.sidebar:
    st.markdown("### 🐱 Tabby English")
    st.caption("막힌 자리에 다음 표현을 띄워주는 영어 회화 코치")
    st.divider()

    if scenario_chosen:
        st.markdown(f"**시나리오**\n\n`{current_scenario}`")
        if mode_chosen:
            mode_label = "⌨️ 키보드" if current_mode == "keyboard" else "🎤 음성"
            st.markdown(f"**입력 방식**: {mode_label}")
        st.caption(f"세션 ID: `{thread_id}`")
        st.divider()

        if st.button("🔄 새 세션 시작", use_container_width=True):
            new_id = f"web_{uuid.uuid4().hex[:8]}"
            st.query_params["thread"] = new_id
            st.rerun()
    else:
        st.caption("왼쪽 위의 페이지 메뉴로 학습 이력도 확인할 수 있어요.")


# ─── 메인 영역: 4가지 화면 분기 ───

if session_ended:
    # ── 화면 4: 세션 종료 후 피드백 ──
    st.markdown("# 🐱 Tabby English")
    st.success("세션이 종료되었습니다. 학습 결과를 확인해보세요.")
    st.divider()

    render_feedback(feedback)

    st.divider()
    if st.button("🔄 새 세션 시작하기", type="primary", use_container_width=True):
        new_id = f"web_{uuid.uuid4().hex[:8]}"
        st.query_params["thread"] = new_id
        st.rerun()

elif not scenario_chosen:
    # ── 화면 1: 시나리오 선택 ──
    st.markdown("# 🐱 Tabby English")
    st.markdown(
        "IDE의 자동완성처럼, 영어로 말하다 막히는 순간 다음 표현을 띄워주는 회화 코치."
    )
    st.write("")

    chosen = render_scenario_picker()
    if chosen:
        app.invoke(make_initial_state(chosen), config=config)
        st.rerun()

elif not mode_chosen:
    # ── 화면 2: 입력 모드 선택 ──
    st.markdown("# 🐱 Tabby English")
    st.write("")

    chosen_mode = render_input_mode_picker(current_scenario)
    if chosen_mode:
        app.update_state(config, {"input_mode": chosen_mode})
        st.rerun()

elif current_mode == "voice":
    # ── 화면 3-A: 음성 모드 ──
    for entry in history:
        role = "user" if entry["role"] == "user" else "assistant"
        avatar = "🧑" if role == "user" else "🤖"
        with st.chat_message(role, avatar=avatar):
            st.write(entry["text"])

    # 첫 사용자 안내 (대화 시작 전 한 번만)
    if not history:
        st.info(
            "🎤 마이크 버튼을 눌러 영어로 말해보세요. "
            "잠시 멈추면 다음 표현이 자동으로 떠올라요. **Tab**으로 채택하면 됩니다.",
            icon="✨",
        )
        with st.expander("💡 음성 모드 사용 팁"):
            st.markdown("""
- **Chrome 또는 Edge** 브라우저에서 가장 안정적으로 동작합니다.
- 마이크 권한 요청이 뜨면 **허용**을 선택해주세요.
- 음성 인식이 가끔 다른 단어로 인식될 수 있어요. 입력창에서 **키보드로 직접 수정**할 수 있습니다.
- 추천이 마음에 들지 않으면 계속 말씀하시거나 입력창을 편집하면 사라집니다.
- 작은 발음 차이도 영어로 인식되도록 가급적 **천천히, 또박또박** 말씀해보세요.
""")

    # 음성 모드 상태 관리용 session_state 초기화
    st.session_state.setdefault("voice_ghost", "")
    st.session_state.setdefault("voice_last_nonce", 0)
    st.session_state.setdefault("voice_reset_nonce", 0)

    # 키보드 모드로 전환할 수 있는 옵션
    with st.expander("⚙️ 입력 방식 변경"):
        if st.button("⌨️ 키보드 모드로 전환"):
            app.update_state(config, {"input_mode": "keyboard"})
            st.session_state.voice_ghost = ""
            st.session_state.voice_last_nonce = 0
            st.rerun()

    msg = ghost_input(
        default_value="",
        ghost_text=st.session_state.voice_ghost,
        input_mode="voice",
        reset_nonce=st.session_state.voice_reset_nonce,
        key="main_voice_input",
    )

    # 음성 인식 에러 시 fallback 안내
    if st.session_state.get("voice_error_occurred"):
        st.warning(
            "🎤 음성 인식에 문제가 있어요.\n\n"
            "- Chrome 또는 Edge 브라우저를 사용하고 계신가요?\n"
            "- 마이크 권한을 허용하셨나요? (브라우저 주소창 좌측 자물쇠 아이콘에서 확인)\n"
            "- 인터넷 연결은 정상인가요?\n\n"
            "계속 안 되시면 키보드 모드로 전환해서 진행하실 수 있어요.",
            icon="⚠️",
        )
        col_kbd, col_retry = st.columns(2)
        with col_kbd:
            if st.button(
                "⌨️ 키보드 모드로 전환", type="primary", use_container_width=True
            ):
                app.update_state(config, {"input_mode": "keyboard"})
                st.session_state.voice_ghost = ""
                st.session_state.voice_last_nonce = 0
                st.session_state.voice_reset_nonce = 0
                st.session_state["voice_error_occurred"] = False
                st.rerun()
        with col_retry:
            if st.button("🔄 다시 시도", use_container_width=True):
                st.session_state["voice_error_occurred"] = False
                st.rerun()

    # 메시지 처리 — 새 메시지만 (nonce로 중복 방지)
    is_new = msg["nonce"] > st.session_state.voice_last_nonce
    if is_new:
        st.session_state.voice_last_nonce = msg["nonce"]

        if msg["type"] == "request_ghost":
            with st.spinner("추천 생성 중..."):
                result = app.invoke(
                    {"raw_input": "", "partial_input": msg["text"]},
                    config=config,
                )
            new_suggestions = result.get("ghost_suggestions", []) if result else []
            if new_suggestions:
                first = new_suggestions[0]
                partial = msg["text"].rstrip()
                # 미완성 끝과 추천 첫 글자가 자연스럽게 이어지도록 공백 정리
                if partial and not first.startswith(" "):
                    st.session_state.voice_ghost = " " + first
                else:
                    st.session_state.voice_ghost = first
            else:
                st.session_state.voice_ghost = ""
            st.rerun()

        elif msg["type"] == "ghost_accepted":
            st.session_state.voice_ghost = ""
            st.rerun()

        elif msg["type"] == "submit":
            with st.spinner("Partner가 응답 중..."):
                app.invoke(
                    {"raw_input": msg["text"], "partial_input": ""},
                    config=config,
                )
            app.update_state(config, {"ghost_suggestions": []})
            st.session_state.voice_ghost = ""
            # reset_nonce를 증가시켜 컴포넌트가 입력창을 비우도록 신호
            st.session_state.voice_reset_nonce += 1
            st.rerun()

        elif msg["type"] == "voice_error":
            st.session_state["voice_error_occurred"] = True

else:
    # ── 화면 3-B: 키보드 모드 ──
    for entry in history:
        role = "user" if entry["role"] == "user" else "assistant"
        avatar = "🧑" if role == "user" else "🤖"
        with st.chat_message(role, avatar=avatar):
            st.write(entry["text"])

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

    # 위젯이 그려지기 전에 입력창 초기값 결정
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

    # 입력 영역 (form으로 Enter 키 전송 지원)
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

    if send_clicked and current_text.strip():
        with st.spinner("Partner가 응답 중..."):
            cast(
                ConversationState,
                app.invoke(
                    {"raw_input": current_text, "partial_input": ""},
                    config=config,
                ),
            )
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
