"""피드백 결과 표시 — 탭과 카드로 가독성 있게 보여준다.

generate_feedback 노드가 만든 JSON을 받아 시각적으로 렌더링.
세션 종료 시 사용된다.
"""

from typing import Any

import streamlit as st


def render_feedback(feedback: dict[str, Any]) -> None:
    """피드백 dict를 3개 탭으로 시각화.

    feedback 형태:
    {
      "summary": "전체 요약",
      "improvements": [{"original": "...", "suggestion": "...", "reason": "..."}],
      "good_points": ["..."]
    }
    """
    if not feedback:
        st.info("아직 피드백이 없습니다. 'end'를 입력해 세션을 마무리해보세요.")
        return

    st.markdown("## 📝 학습 피드백")

    summary = feedback.get("summary", "")
    improvements = feedback.get("improvements", [])
    good_points = feedback.get("good_points", [])

    tab1, tab2, tab3 = st.tabs(
        [
            f"📌 요약",
            f"🔧 개선점 ({len(improvements)})",
            f"✨ 잘한 점 ({len(good_points)})",
        ]
    )

    with tab1:
        if summary:
            st.markdown(
                f"<div style='padding:16px; border-radius:10px; "
                f"background:#f4f3fa; line-height:1.6;'>{summary}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.caption("요약 정보가 없습니다.")

    with tab2:
        if not improvements:
            st.caption("개선할 점이 없는 깔끔한 대화였어요! 👍")
        else:
            for idx, imp in enumerate(improvements, start=1):
                _render_improvement_card(idx, imp)

    with tab3:
        if not good_points:
            st.caption("잘한 점 정보가 없습니다.")
        else:
            for idx, point in enumerate(good_points, start=1):
                st.markdown(
                    f"<div style='padding:12px 14px; border-radius:8px; "
                    f"background:#f0f9f4; border-left:3px solid #44c97c; "
                    f"margin-bottom:8px;'>"
                    f"<span style='color:#44c97c; font-weight:600;'>{idx}.</span> {point}"
                    f"</div>",
                    unsafe_allow_html=True,
                )


def _render_improvement_card(idx: int, imp: dict[str, str]) -> None:
    """단일 개선점 카드."""
    original = imp.get("original", "")
    suggestion = imp.get("suggestion", "")
    reason = imp.get("reason", "")

    st.markdown(
        f"<div style='padding:14px 16px; border-radius:10px; "
        f"background:#fdf6f0; border-left:3px solid #f29856; "
        f"margin-bottom:10px;'>"
        f"<div style='font-weight:600; color:#f29856; margin-bottom:6px;'>"
        f"개선 {idx}</div>"
        f"<div style='font-size:13px; color:#888; margin-bottom:2px;'>원문</div>"
        f"<div style='margin-bottom:8px;'>{original}</div>"
        f"<div style='font-size:13px; color:#888; margin-bottom:2px;'>제안</div>"
        f"<div style='color:#7c6ef2; font-weight:500; margin-bottom:8px;'>{suggestion}</div>"
        f"<div style='font-size:13px; color:#888; margin-bottom:2px;'>이유</div>"
        f"<div style='font-size:14px; color:#555;'>{reason}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
