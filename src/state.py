"""대화 전반에서 공유되는 상태(State) 정의."""

from operator import add
from typing import Annotated, Any, List, Literal, TypedDict

Role = Literal["user", "assistant"]
Signal = Literal["utterance", "silence", "end_session"]


class Utterance(TypedDict):
    role: Role
    text: str
    timestamp: str


class Improvement(TypedDict):
    original: str
    suggestion: str
    reason: str


class Feedback(TypedDict, total=False):
    summary: str
    improvements: List[Improvement]
    good_points: List[str]
    raw_response: str


class ConversationState(TypedDict):
    # 시나리오
    scenario: str
    system_prompt: str

    # 입력 (매 턴 갱신)
    raw_input: str
    input_signal: Signal

    # 누적 (Annotated[List, add]로 자동 append)
    conversation_history: Annotated[List[Utterance], add]

    # generate_ghost ↔ tool_node 간 메시지 교환용.
    # ToolNode가 표준으로 기대하는 필드 이름 'messages'를 사용한다.
    # AIMessage(tool_calls 포함) → ToolMessage(결과) 형태로 누적된다.
    messages: Annotated[List[Any], add]

    # 매 턴의 결과
    last_ai_response: str
    ghost_suggestions: List[str]

    # 종료 시
    feedback: Feedback


class StateUpdate(TypedDict, total=False):
    """노드가 반환할 수 있는 부분 업데이트."""

    system_prompt: str
    input_signal: Signal
    conversation_history: List[Utterance]
    messages: List[Any]
    last_ai_response: str
    ghost_suggestions: List[str]
    feedback: Feedback
