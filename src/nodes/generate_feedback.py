"""generate_feedback 노드: 전체 대화를 LLM에 넘겨 피드백 생성."""

import json
from typing import List, Optional, cast

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from src.prompts import FEEDBACK_PROMPT
from src.state import ConversationState, Feedback, StateUpdate, Utterance

# LLM은 첫 호출 시점에 생성 (lazy init).
# 모듈 로드 시점에 만들면 API 키가 없을 때 import 자체가 실패하므로,
# LLM을 호출하지 않는 노드/테스트가 영향을 받는다.
_llm: Optional[ChatOpenAI] = None


def _get_llm() -> ChatOpenAI:
    """ChatOpenAI 인스턴스를 첫 호출 시 한 번만 생성한다.

    Phase 1에서는 비용이 낮은 gpt-4o-mini 사용.
    response_format으로 JSON 모드를 켜면 파싱이 안정적이다.
    """
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            max_tokens=1024,
            model_kwargs={
                "response_format": {"type": "json_object"},
            },
        )
    return _llm


def generate_feedback_node(state: ConversationState) -> StateUpdate:
    """대화 종료 후 학습 피드백을 LLM으로 생성한다."""
    history: List[Utterance] = state.get("conversation_history", [])

    # 발화가 하나도 없으면 빈 피드백 반환 (LLM 호출 생략)
    if not history:
        empty_feedback: Feedback = {
            "summary": "대화 내용이 없어 피드백을 생성할 수 없습니다.",
            "improvements": [],
            "good_points": [],
        }
        return {"feedback": empty_feedback}

    utterances: str = "\n".join(f"- {entry['text']}" for entry in history)
    prompt: str = FEEDBACK_PROMPT.format(
        scenario=state["scenario"],
        utterances=utterances,
    )

    response = _get_llm().invoke([HumanMessage(content=prompt)])
    feedback: Feedback = _safe_parse_json(str(response.content))

    return {"feedback": feedback}


def _safe_parse_json(text: str) -> Feedback:
    """LLM 응답에서 JSON을 안전하게 파싱한다.

    OpenAI의 JSON 모드를 사용하면 거의 실패하지 않지만,
    혹시 모를 예외 상황에 대비한 방어 코드.
    """
    try:
        data = json.loads(text)
        return cast(Feedback, data)
    except json.JSONDecodeError:
        return {
            "summary": "피드백 파싱에 실패했습니다.",
            "raw_response": text,
            "improvements": [],
            "good_points": [],
        }
