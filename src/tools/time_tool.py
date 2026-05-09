"""현재 시간대 조회 도구."""

from datetime import datetime

from langchain_core.tools import tool


@tool
def get_time_of_day() -> str:
    """현재 시간대를 morning/afternoon/evening 중 하나로 반환한다.

    카페 시나리오에서 시간대에 맞는 메뉴를 추천할 때 사용하라.
    """
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 18:
        return "afternoon"
    return "evening"
