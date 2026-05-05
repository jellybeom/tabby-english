"""analyze_utterance 노드: 발화를 conversation_history에 누적."""

from datetime import datetime

from src.state import ConversationState, StateUpdate, Utterance


def analyze_utterance_node(state: ConversationState) -> StateUpdate:
    """현재 발화를 history에 추가한다.

    State의 conversation_history는 Annotated[List, add]이므로
    리스트를 반환하면 자동으로 append된다 (덮어쓰지 않음).
    """
    raw: str = state["raw_input"].strip()

    # 빈 입력이나 종료 명령어는 history에 쌓지 않음
    if not raw or raw.lower() == "end":
        return {}

    new_entry: Utterance = {
        "role": "user",
        "text": raw,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }

    return {"conversation_history": [new_entry]}
