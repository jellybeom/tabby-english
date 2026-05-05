"""LangGraph StateGraph 조립.

흐름:
    START → setup_scenario → receive_input → analyze_utterance →
        (session_ended? Yes → generate_feedback → END)
        (session_ended? No  → generate_ai_response → END for this turn)

한 번의 app.invoke()는 '한 턴'에 해당한다.
대화 루프는 main.ipynb가 관리하며, 각 턴마다 그래프를 다시 호출한다.
"""

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.nodes import (
    analyze_utterance_node,
    generate_ai_response_node,
    generate_feedback_node,
    receive_input_node,
    setup_scenario_node,
)
from src.state import ConversationState


def _route_after_analyze(state: ConversationState) -> str:
    """analyze_utterance 이후 분기.

    종료 신호가 들어왔으면 피드백 노드로,
    아니면 AI 응답 생성 노드로.
    """
    if state.get("session_ended", False):
        return "generate_feedback"
    return "generate_ai_response"


def build_graph() -> CompiledStateGraph:
    """StateGraph를 빌드하고 컴파일된 앱을 반환한다."""
    workflow: StateGraph = StateGraph(ConversationState)

    # 노드 등록
    workflow.add_node("setup_scenario", setup_scenario_node)
    workflow.add_node("receive_input", receive_input_node)
    workflow.add_node("analyze_utterance", analyze_utterance_node)
    workflow.add_node("generate_ai_response", generate_ai_response_node)
    workflow.add_node("generate_feedback", generate_feedback_node)

    # 진입점
    workflow.set_entry_point("setup_scenario")

    # 일반 엣지
    workflow.add_edge("setup_scenario", "receive_input")
    workflow.add_edge("receive_input", "analyze_utterance")
    workflow.add_edge("generate_ai_response", END)
    workflow.add_edge("generate_feedback", END)

    # 조건부 엣지
    workflow.add_conditional_edges(
        "analyze_utterance",
        _route_after_analyze,
        {
            "generate_ai_response": "generate_ai_response",
            "generate_feedback": "generate_feedback",
        },
    )

    return workflow.compile()
