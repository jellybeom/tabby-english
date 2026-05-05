"""setup_scenario 노드: 시나리오 정보로 system prompt 구성."""

from src.prompts import AI_PARTNER_SYSTEM_PROMPT
from src.state import ConversationState, StateUpdate


def setup_scenario_node(state: ConversationState) -> StateUpdate:
    """시나리오를 받아 AI 대화 상대용 system prompt를 빌드한다.

    LLM 호출 없음. 단순 템플릿 채우기.
    실제 LLM 호출 시 generate_ai_response가 이 prompt를 사용한다.
    """
    system_prompt: str = AI_PARTNER_SYSTEM_PROMPT.format(scenario=state["scenario"])

    return {"system_prompt": system_prompt}
