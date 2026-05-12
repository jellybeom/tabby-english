"""학습 이력 대시보드 페이지.

data/sessions.db의 learning_sessions 테이블을 읽어 시각화한다.
- 누적 통계
- 시나리오별 분포 (도넛 차트)
- 최근 세션 목록
- 자주 지적된 개선 패턴
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path("data/sessions.db")

st.set_page_config(
    page_title="학습 이력 — Tabby English",
    page_icon="📊",
    layout="wide",
)

st.markdown("## 📊 학습 이력 대시보드")
st.caption("종료한 세션들의 누적 학습 기록을 보여줍니다.")

# 배포 환경 안내: Streamlit Cloud는 컨테이너 재시작 시 파일이 사라짐
with st.expander("ℹ️ 학습 이력은 영구 저장되지 않을 수 있어요"):
    st.markdown(
        "이 앱은 학습 이력을 로컬 SQLite에 저장합니다. "
        "**Streamlit Cloud 배포 환경**에서는 앱이 일정 시간 비활성이거나 "
        "재배포되면 컨테이너가 재시작되면서 이력이 초기화될 수 있습니다.\n\n"
        "장기 학습 추적이 필요하면 로컬에서 실행해주세요. "
        "데모 환경에서는 한 세션 동안의 기록만 보장됩니다."
    )


# ─── DB 로드 ───
def _load_sessions() -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    with sqlite3.connect(DB_PATH) as conn:
        table_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='learning_sessions'"
        ).fetchone()
        if not table_exists:
            return pd.DataFrame()
        return pd.read_sql_query(
            "SELECT id, ended_at, scenario, turn_count, feedback "
            "FROM learning_sessions ORDER BY id DESC",
            conn,
        )


df = _load_sessions()

if df.empty:
    st.info(
        "아직 종료된 세션이 없습니다.\n\n"
        "메인 페이지에서 영어 대화를 진행하고 `end`로 마무리하면 여기에 기록이 쌓여요."
    )
    st.stop()


# ─── 누적 통계 ───
total_sessions = len(df)
total_turns = int(df["turn_count"].sum())
unique_scenarios = df["scenario"].nunique()

# 피드백에서 improvements와 good_points 개수 추출
all_improvements: list[str] = []
total_good = 0
for fb_json in df["feedback"]:
    try:
        fb = json.loads(fb_json)
    except (json.JSONDecodeError, TypeError):
        continue
    for imp in fb.get("improvements", []):
        all_improvements.append(imp.get("original", ""))
    total_good += len(fb.get("good_points", []))

col1, col2, col3, col4 = st.columns(4)
col1.metric("누적 세션", f"{total_sessions}")
col2.metric("총 대화 턴", f"{total_turns}")
col3.metric("시도한 시나리오", f"{unique_scenarios}")
col4.metric("받은 칭찬", f"{total_good}")

st.divider()


# ─── 시나리오별 분포 ───
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 🎭 시나리오별 학습 분포")
    scenario_counts = df["scenario"].value_counts()
    st.bar_chart(scenario_counts, height=260)

with col_right:
    st.markdown("### 📅 최근 세션 5개")
    recent = df.head(5)[["ended_at", "scenario", "turn_count"]].copy()
    recent.columns = ["종료 시각", "시나리오", "턴 수"]
    recent["종료 시각"] = recent["종료 시각"].str.replace("T", " ").str[:16]
    st.dataframe(recent, hide_index=True, use_container_width=True)


# ─── 자주 지적된 개선 패턴 ───
st.divider()
st.markdown("### 🔍 자주 지적된 표현 (개선 대상)")

if all_improvements:
    counter = Counter(all_improvements)
    top_5 = counter.most_common(5)

    for rank, (phrase, count) in enumerate(top_5, start=1):
        st.markdown(
            f"<div style='padding:10px 14px; border-radius:8px; "
            f"background:#fdf6f0; border-left:3px solid #f29856; "
            f"margin-bottom:6px; display:flex; justify-content:space-between;'>"
            f"<span><b>{rank}.</b> {phrase}</span>"
            f"<span style='color:#f29856; font-weight:600;'>×{count}회</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
else:
    st.caption("아직 개선 지적이 없거나, 모든 표현이 한 번씩만 지적되었어요.")
