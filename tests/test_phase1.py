"""Phase 1 동작 검증용 간단한 테스트.

LLM 호출 없이 그래프 구조와 State 누적이 제대로 작동하는지 확인한다.
실행: python -m tests.test_phase1
"""

from src.nodes.analyze_utterance import analyze_utterance_node
from src.nodes.receive_input import receive_input_node
from src.nodes.setup_scenario import setup_scenario_node


def test_setup_scenario():
    """system_prompt에 시나리오가 주입되는지."""
    result = setup_scenario_node({"scenario": "cafe"})
    assert "cafe" in result["system_prompt"]
    print("✓ setup_scenario_node")


def test_receive_input_normal():
    """일반 입력은 session_ended=False."""
    result = receive_input_node({"raw_input": "Hello"})
    assert result["session_ended"] is False
    print("✓ receive_input_node (normal)")


def test_receive_input_end():
    """'end' 입력은 session_ended=True."""
    result = receive_input_node({"raw_input": "end"})
    assert result["session_ended"] is True
    print("✓ receive_input_node (end command)")


def test_analyze_appends():
    """발화가 history에 누적되는 형태인지."""
    result = analyze_utterance_node({"raw_input": "I went to the cafe"})
    assert "conversation_history" in result
    assert len(result["conversation_history"]) == 1
    assert result["conversation_history"][0]["text"] == "I went to the cafe"
    print("✓ analyze_utterance_node (appends entry)")


def test_analyze_skips_empty():
    """빈 입력이나 'end'는 history에 쌓지 않음."""
    assert analyze_utterance_node({"raw_input": ""}) == {}
    assert analyze_utterance_node({"raw_input": "end"}) == {}
    print("✓ analyze_utterance_node (skips empty/end)")


if __name__ == "__main__":
    test_setup_scenario()
    test_receive_input_normal()
    test_receive_input_end()
    test_analyze_appends()
    test_analyze_skips_empty()
    print("\n모든 테스트 통과!")
