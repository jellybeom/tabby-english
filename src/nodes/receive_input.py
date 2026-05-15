"""receive_input 노드: 입력을 보고 signal을 결정한다.

신호 판단 규칙:
- "end"             → end_session
- "" (빈 raw_input) → silence
  · partial_input이 있으면 "중간에 막힘" 케이스
  · 없으면 "처음부터 막힘" 케이스
- 그 외             → utterance

외부(UI)는 raw_input과 partial_input만 채우고, 신호 판단은 노드 안에서 처리한다.
"""

from src.state import ConversationState, StateUpdate


def receive_input_node(state: ConversationState) -> StateUpdate:
    raw = state.get("raw_input", "").strip()

    if raw.lower() == "end":
        return {"input_signal": "end_session"}
    if raw == "":
        return {"input_signal": "silence"}
    return {"input_signal": "utterance"}
