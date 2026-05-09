"""사용자의 과거 학습 이력에서 자주 지적된 개선점을 조회하는 도구.

LLM은 이번 세션의 대화만 알 수 있다. 이전 세션에서 어떤 실수를 반복했는지는
DB에 저장되어 있고 LLM은 절대 알 수 없으므로, 이 도구로 정보를 얻어야 한다.
"""

import json
import sqlite3
from pathlib import Path
from typing import List

from langchain_core.tools import tool

DB_PATH = Path("data/sessions.db")


@tool
def get_user_weak_points() -> str:
    """과거 학습 세션에서 자주 지적되었던 개선점 표현들을 반환한다.

    추천을 만들기 전에 호출하면, 학습자가 자주 틀리는 패턴을 피해
    더 도움이 되는 표현을 제안할 수 있다.
    """
    if not DB_PATH.exists():
        return "(아직 학습 이력이 없습니다.)"

    with sqlite3.connect(DB_PATH) as conn:
        # 테이블이 없는 경우 방어
        table_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='learning_sessions'"
        ).fetchone()
        if not table_exists:
            return "(아직 학습 이력이 없습니다.)"

        rows = conn.execute(
            "SELECT feedback FROM learning_sessions ORDER BY id DESC LIMIT 5"
        ).fetchall()

    weak_points: List[str] = []
    for (fb_json,) in rows:
        try:
            feedback = json.loads(fb_json)
        except json.JSONDecodeError:
            continue
        for imp in feedback.get("improvements", []):
            weak_points.append(f"{imp['original']} → {imp['suggestion']}")

    if not weak_points:
        return "(아직 지적된 개선점이 없습니다.)"

    return "최근 자주 지적된 개선점: " + " / ".join(weak_points[:5])
