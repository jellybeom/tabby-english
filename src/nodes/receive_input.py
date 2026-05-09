"""receive_input 노드: 입력을 보고 signal을 결정한다.

입력의 내용에 따라 세 가지 signal 중 하나를 정한다:
- "end_session": 입력이 'end'
- "silence":     입력이 빈 문자열 (머뭇거림)
- "utterance":   그 외 (일반 발화)

옵션 B 방식 — 외부(노트북/프론트)는 raw_input만 채우고,
신호 판단은 LangGraph 안에서 처리한다. 이렇게 하면 향후 음성/VAD가 붙어도
프론트는 raw_input만 흘려보내면 되고, 분기 로직은 그래프 안에 일관되게 머문다.
"""

from src.state import ConversationState, StateUpdate


def receive_input_node(state: ConversationState) -> StateUpdate:
    raw = state.get("raw_input", "").strip()

    if raw.lower() == "end":
        return {"input_signal": "end_session"}
    if raw == "":
        return {"input_signal": "silence"}
    return {"input_signal": "utterance"}
