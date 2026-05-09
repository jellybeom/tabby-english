"""persist_session 노드: 세션 종료 시 학습 이력을 SQLite에 저장.

Checkpointer가 매 턴의 State를 자동 저장한다면,
이 노드는 사람이 보기 좋은 형태로 학습 기록을 남긴다.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from src.state import ConversationState, StateUpdate

DB_PATH = Path("data/sessions.db")


def _ensure_table() -> None:
    DB_PATH.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS learning_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ended_at TEXT NOT NULL,
                scenario TEXT NOT NULL,
                turn_count INTEGER NOT NULL,
                conversation TEXT NOT NULL,
                feedback TEXT NOT NULL
            )
        """)


def persist_session_node(state: ConversationState) -> StateUpdate:
    _ensure_table()

    history = state.get("conversation_history", [])
    user_turns = sum(1 for e in history if e["role"] == "user")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO learning_sessions "
            "(ended_at, scenario, turn_count, conversation, feedback) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                datetime.now().isoformat(timespec="seconds"),
                state["scenario"],
                user_turns,
                json.dumps(history, ensure_ascii=False),
                json.dumps(state.get("feedback", {}), ensure_ascii=False),
            ),
        )

    return {}  # State 변경 없음
