"""Phase 2 동작 검증.

LLM 호출 없이 노드의 분기 로직과 도구 정의를 검증한다.
실행: uv run python -m tests.test_phase2
"""

from src.nodes.analyze_utterance import analyze_utterance_node
from src.nodes.receive_input import receive_input_node
from src.nodes.setup_scenario import setup_scenario_node
from src.tools import ALL_TOOLS
from src.tools.time_tool import get_time_of_day
from src.tools.weak_points_tool import get_user_weak_points


def test_setup_scenario():
    result = setup_scenario_node({"scenario": "cafe"})
    assert "cafe" in result["system_prompt"]
    print("✓ setup_scenario")


def test_receive_input_signals():
    """입력에 따라 signal이 정확히 결정되는지."""
    assert receive_input_node({"raw_input": "Hello"})["input_signal"] == "utterance"
    assert receive_input_node({"raw_input": ""})["input_signal"] == "silence"
    assert receive_input_node({"raw_input": "   "})["input_signal"] == "silence"
    assert receive_input_node({"raw_input": "end"})["input_signal"] == "end_session"
    assert receive_input_node({"raw_input": "END"})["input_signal"] == "end_session"
    print("✓ receive_input (3가지 signal)")


def test_analyze_appends():
    result = analyze_utterance_node({"raw_input": "I went to the cafe"})
    assert len(result["conversation_history"]) == 1
    assert result["conversation_history"][0]["text"] == "I went to the cafe"
    assert result["conversation_history"][0]["role"] == "user"
    print("✓ analyze_utterance (append)")


def test_tools_registered():
    assert len(ALL_TOOLS) == 2
    tool_names = {t.name for t in ALL_TOOLS}
    assert "get_time_of_day" in tool_names
    assert "get_user_weak_points" in tool_names
    print("✓ tools 등록 (2개)")


def test_get_time_of_day():
    result = get_time_of_day.invoke({})
    assert result in ("morning", "afternoon", "evening")
    print("✓ get_time_of_day 실행")


def test_get_user_weak_points():
    """DB가 없을 때도 안전하게 메시지 반환."""
    result = get_user_weak_points.invoke({})
    # DB 유무에 따라 반환값이 다름. 둘 다 문자열이면 OK.
    assert isinstance(result, str)
    assert len(result) > 0
    print("✓ get_user_weak_points 실행 (DB 없을 때 안전)")


def test_route_by_signal():
    """그래프의 signal 기반 라우터가 정확히 분기하는지."""
    from src.graph import _route_by_signal

    assert _route_by_signal({"input_signal": "utterance"}) == "analyze_utterance"
    assert _route_by_signal({"input_signal": "silence"}) == "generate_ghost"
    assert _route_by_signal({"input_signal": "end_session"}) == "generate_feedback"
    print("✓ router (signal 분기)")


if __name__ == "__main__":
    test_setup_scenario()
    test_receive_input_signals()
    test_analyze_appends()
    test_tools_registered()
    test_get_time_of_day()
    test_get_user_weak_points()
    test_route_by_signal()
    print("\n모든 테스트 통과!")
