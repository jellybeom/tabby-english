"""generate_ghost 노드: 머뭇거릴 때 다음 표현 추천.

- 노드 진입 시 도구(get_time_of_day, get_user_weak_points)를 직접 호출해
  컨텍스트 정보를 수집한다.
- 그 결과를 프롬프트에 주입한 뒤 LLM을 단 1회 호출한다.
- LLM이 만든 추천이 미완성 입력과 단어 중복을 일으키면 후처리로 자동 보정한다.
"""

import json
import re
from typing import List, Optional

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from src.prompts import GHOST_SUGGESTION_PROMPT
from src.state import ConversationState, StateUpdate, Utterance
from src.tools.time_tool import get_time_of_day
from src.tools.weak_points_tool import get_user_weak_points

_llm: Optional[ChatOpenAI] = None


def _get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)
    return _llm


def _format_history(history: List[Utterance]) -> str:
    if not history:
        return "(아직 대화 없음)"
    lines = []
    for entry in history[-6:]:
        speaker = "You" if entry["role"] == "user" else "Partner"
        lines.append(f"{speaker}: {entry['text']}")
    return "\n".join(lines)


def _collect_tool_context() -> str:
    """도구를 직접 호출해 LLM에 주입할 컨텍스트 정보를 만든다."""
    time_info = get_time_of_day.invoke({})
    weak_info = get_user_weak_points.invoke({})
    return f"- 현재 시간대: {time_info}\n- 학습자 약점 정보: {weak_info}"


def generate_ghost_node(state: ConversationState) -> StateUpdate:
    """추천어 3개 생성. 도구 호출은 노드가 직접 처리."""
    history = state.get("conversation_history", [])
    partial = state.get("partial_input", "").strip()

    # 직전 발화자 파악
    if history and history[-1]["role"] == "assistant":
        last_speaker = "Partner (직전에 Partner가 말했음)"
    elif history:
        last_speaker = "You (You가 이어서 말하는 중)"
    else:
        last_speaker = "없음 (You가 대화를 시작)"

    # 도구 정보 수집 (항상 호출 — 비용 매우 낮음)
    tool_context = _collect_tool_context()

    prompt = GHOST_SUGGESTION_PROMPT.format(
        scenario=state["scenario"],
        history=_format_history(history),
        partial=partial if partial else "(없음 - 처음부터 시작)",
        last_speaker=last_speaker,
        tool_context=tool_context,
    )

    response = _get_llm().invoke([HumanMessage(content=prompt)])
    suggestions = _parse_suggestions(str(response.content))

    # 합치기 검증: partial과 합쳤을 때 단어 중복이 생기는 추천은 자동 보정
    if partial:
        suggestions = [_dedupe_overlap(partial, s) for s in suggestions]

    return {"ghost_suggestions": suggestions}


def _dedupe_overlap(partial: str, suggestion: str) -> str:
    """미완성과 추천이 합쳐졌을 때 단어가 중복되면 추천의 앞부분을 제거.

    단어 1개 중복뿐 아니라 여러 단어 중복도 처리:
    - "I think that's" + "that's all for now" → "all for now"
    - "Can I" + "Can I have the bill" → "have the bill"
    """
    partial_words = [w.lower().rstrip(".,!?") for w in partial.strip().split()]
    suggestion_words = suggestion.strip().split()
    if not partial_words or not suggestion_words:
        return suggestion

    suggestion_lower = [w.lower().rstrip(".,!?") for w in suggestion_words]

    # 최대 중복 길이 = min(partial 길이, suggestion 길이)
    max_overlap = min(len(partial_words), len(suggestion_words))

    # 가장 긴 중복부터 검사하여 첫 매치를 채택
    for overlap_len in range(max_overlap, 0, -1):
        partial_tail = partial_words[-overlap_len:]
        suggestion_head = suggestion_lower[:overlap_len]
        if partial_tail == suggestion_head and overlap_len < len(suggestion_words):
            return " ".join(suggestion_words[overlap_len:])

    return suggestion


def _parse_suggestions(text: str) -> List[str]:
    """LLM 응답에서 JSON 배열을 추출. 설명 문장이 섞여 있어도 정확히 분리."""
    text = text.strip()

    if "```" in text:
        match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
        if match:
            text = match.group(1)

    match = re.search(r"\[\s*\".*?\"\s*(?:,\s*\".*?\"\s*)*\]", text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, list):
                return [str(s) for s in parsed][:3]
        except json.JSONDecodeError:
            pass

    lines = [line.strip("- *•").strip() for line in text.splitlines()]
    lines = [line for line in lines if line and len(line) < 100]
    if lines:
        return lines[:3]

    return [text]
