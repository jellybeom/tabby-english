"""LangGraph StateGraph 조립.

핵심 학습 요소:
1. Conditional edges — receive_input 후 signal에 따라 3갈래 분기
2. Checkpointer    — SqliteSaver로 모든 상태 전이 자동 저장

도구 호출은 generate_ghost 노드 내부에서 직접 처리한다 (ToolNode 미사용).
이렇게 한 이유:
- 한 번의 invoke = 한 사이클의 깔끔한 시작/끝
- messages 누적 등 부가 상태 관리 불필요
- 추천 품질이 일관적

학습 측면에서 ToolNode/ReAct 패턴은 Phase 2 초기 버전에서 다뤘다.
"""

import os
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

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

CHECKPOINT_DB = "data/checkpoints.db"


def _route_by_signal(state: ConversationState) -> str:
    """receive_input 이후 signal에 따라 분기."""
    signal = state.get("input_signal", "utterance")
    return {
        "utterance": "analyze_utterance",
        "silence": "generate_ghost",
        "end_session": "generate_feedback",
    }[signal]


def build_graph() -> CompiledStateGraph:
    """그래프를 빌드하고 Checkpointer와 함께 컴파일한다."""
    workflow: StateGraph = StateGraph(ConversationState)

    # 노드 등록
    workflow.add_node("setup_scenario", setup_scenario_node)
    workflow.add_node("receive_input", receive_input_node)
    workflow.add_node("analyze_utterance", analyze_utterance_node)
    workflow.add_node("generate_ai_response", generate_ai_response_node)
    workflow.add_node("generate_ghost", generate_ghost_node)
    workflow.add_node("generate_feedback", generate_feedback_node)
    workflow.add_node("persist_session", persist_session_node)

    # 진입점
    workflow.set_entry_point("setup_scenario")

    # 일반 엣지
    workflow.add_edge("setup_scenario", "receive_input")
    workflow.add_edge("analyze_utterance", "generate_ai_response")
    workflow.add_edge("generate_ai_response", END)
    workflow.add_edge("generate_ghost", END)
    workflow.add_edge("generate_feedback", "persist_session")
    workflow.add_edge("persist_session", END)

    # 조건부 엣지: signal에 따라 3갈래
    workflow.add_conditional_edges(
        "receive_input",
        _route_by_signal,
        {
            "analyze_utterance": "analyze_utterance",
            "generate_ghost": "generate_ghost",
            "generate_feedback": "generate_feedback",
        },
    )

    # Checkpointer 컴파일
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(CHECKPOINT_DB, check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    return workflow.compile(checkpointer=checkpointer)
