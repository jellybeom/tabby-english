"""ghost_input 커스텀 Streamlit 컴포넌트.

입력창 안에 회색 ghost text를 표시하고, 음성 인식까지 지원하는 입력 위젯.

JS → Python 메시지 타입:
- "request_ghost"  : 키보드 3초 무입력 또는 음성 2.5초 무음 → 추천 요청
- "ghost_accepted" : Tab으로 ghost 채택
- "submit"         : Enter로 메시지 전송
- "voice_error"    : 음성 인식 실패 (마이크 권한 거부 등)
"""

from pathlib import Path
from typing import Any, Literal, Optional, TypedDict

import streamlit.components.v1 as components


class GhostInputMessage(TypedDict):
    """컴포넌트가 반환하는 메시지 형태."""

    type: str
    text: str
    nonce: int


_FRONTEND_DIR = (Path(__file__).parent / "frontend").resolve()

_component_func = components.declare_component(
    "ghost_input",
    path=str(_FRONTEND_DIR),
)


_DEFAULT_MESSAGE: GhostInputMessage = {
    "type": "input_change",
    "text": "",
    "nonce": 0,
}


def ghost_input(
    default_value: str = "",
    ghost_text: str = "",
    input_mode: Literal["keyboard", "voice"] = "keyboard",
    reset_nonce: int = 0,
    key: Optional[str] = None,
) -> GhostInputMessage:
    """ghost_input 컴포넌트를 그리고, 사용자의 현재 상태를 메시지로 반환.

    Args:
        default_value: 첫 렌더 시 입력창에 채울 텍스트
        ghost_text: 입력창 안에 회색으로 표시할 추천
        input_mode: "keyboard" 또는 "voice".
            "voice"일 때만 마이크 버튼이 표시되고 Web Speech API가 활성화된다.
        reset_nonce: 이 값을 증가시키면 컴포넌트가 내부 상태를 초기화한다.
            (예: 메시지 전송 후 입력창을 비울 때 사용)
        key: Streamlit 위젯 식별자

    Returns:
        GhostInputMessage — type 필드로 어떤 이벤트인지 판단
    """
    raw: Any = _component_func(
        default_value=default_value,
        ghost_text=ghost_text,
        input_mode=input_mode,
        reset_nonce=reset_nonce,
        key=key,
        default=_DEFAULT_MESSAGE,
    )

    if isinstance(raw, dict) and "type" in raw:
        return {
            "type": str(raw.get("type", "input_change")),
            "text": str(raw.get("text", "")),
            "nonce": int(raw.get("nonce", 0)),
        }
    return _DEFAULT_MESSAGE.copy()
