"""generate_ghost 노드: 머뭇거릴 때 다음 표현 추천.

LangGraph 표준 패턴:
- State의 messages 필드를 통해 ToolNode와 메시지를 주고받는다.
- LLM이 도구 호출을 결정하면 AIMessage(tool_calls 포함)를 messages에 누적
  → 그래프가 자동으로 tool_node로 분기 → ToolMessage가 messages에 누적
  → 다시 generate_ghost로 돌아오면 누적된 messages를 보고 최종 답변을 만든다.
"""

import json
from typing import List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI

from src.prompts import GHOST_SUGGESTION_PROMPT
from src.state import ConversationState, StateUpdate, Utterance
from src.tools import ALL_TOOLS

_llm: Optional[ChatOpenAI] = None


def _get_llm():
    global _llm
    if _llm is None:
        base = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)
        _llm = base.bind_tools(ALL_TOOLS)  # type: ignore[assignment]
    return _llm


def _format_history(history: List[Utterance]) -> str:
    if not history:
        return "(아직 대화 없음)"
    lines = []
    for entry in history[-6:]:
        speaker = "You" if entry["role"] == "user" else "Partner"
        lines.append(f"{speaker}: {entry['text']}")
    return "\n".join(lines)


def _is_returning_from_tool(messages: List[BaseMessage]) -> bool:
    """messages의 마지막이 ToolMessage면 도구 실행을 마치고 돌아온 상태."""
    return bool(messages) and isinstance(messages[-1], ToolMessage)


def generate_ghost_node(state: ConversationState) -> StateUpdate:
    """LLM 호출. tool 호출이 있으면 messages에 누적, 없으면 ghost_suggestions 채움."""
    existing: List[BaseMessage] = state.get("messages", [])

    if _is_returning_from_tool(existing):
        # 도구 결과를 받고 돌아온 상태: 누적된 messages를 그대로 LLM에 전달
        messages_for_llm = existing
    else:
        # 새 silence 요청: prompt를 새로 만들어 시작.
        # 이전 호출의 잔여 messages가 있어도 무시한다.
        prompt = GHOST_SUGGESTION_PROMPT.format(
            scenario=state["scenario"],
            history=_format_history(state.get("conversation_history", [])),
        )
        messages_for_llm = [HumanMessage(content=prompt)]

    response = _get_llm().invoke(messages_for_llm)

    if isinstance(response, AIMessage) and response.tool_calls:
        # 도구 호출 → messages에 prompt와 응답을 누적해 tool_node로 보낸다.
        # _is_returning_from_tool=True 케이스에서는 이미 messages에 prompt가 있으므로
        # 응답만 추가하면 된다.
        if _is_returning_from_tool(existing):
            return {"messages": [response]}
        return {"messages": list(messages_for_llm) + [response]}

    # 도구 호출 없음 → 최종 응답
    suggestions = _parse_suggestions(str(response.content))
    return {"ghost_suggestions": suggestions}


def _parse_suggestions(text: str) -> List[str]:
    """LLM 응답에서 JSON 배열을 추출한다."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1].lstrip("json").strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(s) for s in parsed][:3]
    except json.JSONDecodeError:
        pass
    return [text]
