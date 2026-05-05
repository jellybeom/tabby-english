"""generate_ai_response 노드: AI가 대화 상대 역할로 응답을 생성한다.

학습자의 가장 최근 발화에 대해, 시나리오에 맞는 대화 상대(카페 직원,
면접관 등) 역할로 자연스러운 영어 응답을 생성한다.
"""

from datetime import datetime
from typing import List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.prompts import AI_PARTNER_SYSTEM_PROMPT
from src.state import ConversationState, StateUpdate, Utterance

# Lazy init — 첫 호출 시점에만 LLM 인스턴스 생성
_llm: Optional[ChatOpenAI] = None


def _get_llm() -> ChatOpenAI:
    """대화 응답용 LLM 인스턴스를 반환한다.

    피드백용과 달리 JSON 모드는 켜지 않는다 (자연스러운 응답이 필요).
    """
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            model_kwargs={"max_tokens": 200},
        )
    return _llm


def generate_ai_response_node(state: ConversationState) -> StateUpdate:
    """학습자의 최근 발화에 대해 AI 대화 상대로서 응답한다."""
    history: List[Utterance] = state.get("conversation_history", [])

    # 학습자가 아무 말도 안 했으면 응답 생략
    if not history or history[-1]["role"] != "user":
        return {}

    # LangChain 메시지 형식으로 변환
    messages = [
        SystemMessage(
            content=AI_PARTNER_SYSTEM_PROMPT.format(scenario=state["scenario"])
        )
    ]
    for entry in history:
        if entry["role"] == "user":
            messages.append(HumanMessage(content=entry["text"]))
        else:
            messages.append(AIMessage(content=entry["text"]))

    response = _get_llm().invoke(messages)
    ai_text: str = str(response.content).strip()

    # 응답을 history에 누적 + 이번 턴 응답을 last_ai_response에 저장
    ai_entry: Utterance = {
        "role": "assistant",
        "text": ai_text,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }

    return {
        "conversation_history": [ai_entry],
        "last_ai_response": ai_text,
    }
