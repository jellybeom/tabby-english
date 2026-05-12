"""대화 전반에서 공유되는 상태(State) 정의."""

from operator import add
from typing import Annotated, List, Literal, TypedDict

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
    raw_input: str  # 완성된 입력 (전송 의도)
    partial_input: str  # 입력창에 타이핑 중인 미완성 텍스트
    input_signal: Signal

    # 누적
    conversation_history: Annotated[List[Utterance], add]

    # 매 턴의 결과
    last_ai_response: str
    ghost_suggestions: List[str]

    # 종료 시
    feedback: Feedback


class StateUpdate(TypedDict, total=False):
    """노드가 반환할 수 있는 부분 업데이트."""

    system_prompt: str
    partial_input: str
    input_signal: Signal
    conversation_history: List[Utterance]
    last_ai_response: str
    ghost_suggestions: List[str]
    feedback: Feedback
