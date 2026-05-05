"""receive_input 노드: 사용자 입력을 받아 State에 반영."""

from src.state import ConversationState, StateUpdate


def receive_input_node(state: ConversationState) -> StateUpdate:
    """raw_input이 있는지 확인하고, 종료 명령어를 감지한다.

    'end'가 입력되면 session_ended를 True로 표시.
    """
    raw: str = state.get("raw_input", "").strip()

    if raw.lower() == "end":
        return {"session_ended": True}

    return {"session_ended": False}
