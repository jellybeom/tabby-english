"""대화 전반에서 공유되는 상태(State) 정의.

LangGraph에서 State는 모든 노드가 함께 들고 다니는 '여행 가방'.
각 노드는 이 가방에서 필요한 것을 꺼내 쓰고, 결과를 가방에 다시 넣는다.
"""

from operator import add
from typing import Annotated, List, Literal, TypedDict

# user: 학습자의 발화 / assistant: AI 대화 상대의 응답
Role = Literal["user", "assistant"]


class Utterance(TypedDict):
    """conversation_history에 누적되는 발화 한 건의 형태."""

    role: Role
    text: str
    timestamp: str  # ISO 8601 형식


class Improvement(TypedDict):
    """피드백의 개선점 한 건."""

    original: str
    suggestion: str
    reason: str


class Feedback(TypedDict, total=False):
    """generate_feedback이 반환하는 피드백 구조."""

    summary: str
    improvements: List[Improvement]
    good_points: List[str]
    raw_response: str  # 파싱 실패 시 원문


class ConversationState(TypedDict):
    """대화 상태 (전체 State).

    Annotated[List, add]는 "덮어쓰지 말고 누적하라"는 의미.
    """

    # ─── 시나리오 (setup 후 변경 없음) ───
    scenario: str
    system_prompt: str

    # ─── 입력 (매 턴 갱신) ───
    raw_input: str
    session_ended: bool

    # ─── 누적 (계속 쌓임) ───
    conversation_history: Annotated[List[Utterance], add]

    # ─── 매 턴의 AI 응답 (UI에서 표시용) ───
    last_ai_response: str

    # ─── 출력 ───
    feedback: Feedback


# ─── 노드별 부분 업데이트 타입 ───


class StateUpdate(TypedDict, total=False):
    """노드가 반환할 수 있는 모든 필드의 부분집합."""

    system_prompt: str
    session_ended: bool
    conversation_history: List[Utterance]
    last_ai_response: str
    feedback: Feedback
