"""generate_ghost 노드가 사용할 LLM 도구 모음.

LLM이 자체적으로 알 수 없는 정보를 외부에서 가져오는 역할:
- get_time_of_day: 현재 시간대 (LLM은 학습 데이터 cutoff 이후의 시간을 모름)
- get_user_weak_points: 사용자의 과거 학습 이력 (LLM은 다른 세션의 정보를 모름)
"""

from src.tools.time_tool import get_time_of_day
from src.tools.weak_points_tool import get_user_weak_points

ALL_TOOLS = [get_time_of_day, get_user_weak_points]
