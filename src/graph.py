"""LangGraph StateGraph 조립 (Phase 2).

세 가지 핵심 학습 요소:
1. Conditional edges — receive_input 후 signal에 따라 3갈래 분기
2. Tool node       — generate_ghost가 도구 호출 시 ToolNode로 갔다가 복귀 (ReAct)
3. Checkpointer    — SqliteSaver로 모든 상태 전이 자동 저장
"""

import os
import sqlite3

from langchain_core.messages import AIMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from src.nodes import (
    analyze_utterance_node,
    generate_ai_response_node,
    generate_feedback_node,
    generate_ghost_node,
    persist_session_node,
    receive_input_node,
    setup_scenario_node,
)
from src.state import ConversationState
from src.tools import ALL_TOOLS

CHECKPOINT_DB = "data/checkpoints.db"


# ─── 라우팅 함수들 ───


def _route_by_signal(state: ConversationState) -> str:
    """receive_input 이후 signal에 따라 분기."""
    signal = state.get("input_signal", "utterance")
    return {
        "utterance": "analyze_utterance",
        "silence": "generate_ghost",
        "end_session": "generate_feedback",
    }[signal]


def _route_after_ghost(state: ConversationState) -> str:
    """generate_ghost 이후 분기.

    messages의 마지막이 tool_calls를 가진 AIMessage면 → tool_node
    그렇지 않으면 (ghost_suggestions가 채워졌다는 뜻) → END
    """
    messages = state.get("messages", [])
    if messages:
        last = messages[-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            return "tools"
    return END


def build_graph() -> CompiledStateGraph:
    """그래프를 빌드하고 Checkpointer와 함께 컴파일한다."""
    workflow: StateGraph = StateGraph(ConversationState)

    # 노드 등록
    workflow.add_node("setup_scenario", setup_scenario_node)
    workflow.add_node("receive_input", receive_input_node)
    workflow.add_node("analyze_utterance", analyze_utterance_node)
    workflow.add_node("generate_ai_response", generate_ai_response_node)
    workflow.add_node("generate_ghost", generate_ghost_node)
    workflow.add_node("tools", ToolNode(ALL_TOOLS))  # 표준 ToolNode 그대로 사용
    workflow.add_node("generate_feedback", generate_feedback_node)
    workflow.add_node("persist_session", persist_session_node)

    # 진입점
    workflow.set_entry_point("setup_scenario")

    # 일반 엣지
    workflow.add_edge("setup_scenario", "receive_input")
    workflow.add_edge("analyze_utterance", "generate_ai_response")
    workflow.add_edge("generate_ai_response", END)
    workflow.add_edge("tools", "generate_ghost")  # 도구 결과를 가지고 ghost로 복귀
    workflow.add_edge("generate_feedback", "persist_session")
    workflow.add_edge("persist_session", END)

    # 조건부 엣지 1: signal에 따라 3갈래
    workflow.add_conditional_edges(
        "receive_input",
        _route_by_signal,
        {
            "analyze_utterance": "analyze_utterance",
            "generate_ghost": "generate_ghost",
            "generate_feedback": "generate_feedback",
        },
    )

    # 조건부 엣지 2: tool 호출 여부에 따라 분기
    workflow.add_conditional_edges(
        "generate_ghost",
        _route_after_ghost,
        {
            "tools": "tools",
            END: END,
        },
    )

    # Checkpointer를 붙여 컴파일
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(CHECKPOINT_DB, check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    return workflow.compile(checkpointer=checkpointer)
