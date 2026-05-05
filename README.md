# Tabby English

> IDE의 자동완성처럼, 영어로 말하다 막히는 순간 다음 표현을 띄워주는 회화 코칭 에이전트

LangGraph로 구현하는 영어회화 학습용 AI 에이전트입니다. 사용자의 영어 발화를 받아 대화 흐름을 관리하고, 머뭇거릴 때 추천어를 제시하며, 대화 종료 후 학습 피드백을 생성합니다.

---

## 📍 프로젝트 단계 (Roadmap)

본 프로젝트는 LangGraph 학습을 주 목적으로 하며, 3단계에 걸쳐 점진적으로 구현합니다.

| 단계        | 핵심 목표                                     | 상태           |
| ----------- | --------------------------------------------- | -------------- |
| **Phase 1** | LangGraph 뼈대 구축 (직선 흐름 + 피드백 생성) | 🚧 **진행 중** |
| **Phase 2** | 조건부 분기 + 추천어 + 세션 영속성            | ⏳ 예정        |
| **Phase 3** | Streamlit UI 통합                             | ⏳ 예정        |

각 단계가 완성된 후에도 기존 코드는 보존되며, 다음 단계는 그 위에 얇게 올라가는 구조로 설계되어 있습니다.

---

## 🎯 Phase 1: 목표와 범위

### 무엇을 만드는가

터미널에서 영어로 대화한 뒤 종료 명령을 입력하면, 전체 대화를 분석한 학습 피드백이 콘솔에 출력되는 최소 동작 LangGraph 파이프라인.

### Phase 1에서 다루는 것

- ✅ LangGraph의 `StateGraph` 구성
- ✅ State / Node / Edge 기본 개념 적용
- ✅ 누적 필드 (`Annotated[List, add]`) 사용
- ✅ LLM 호출 노드 1개 (피드백 생성)
- ✅ 직선형 흐름 + 단순 종료 분기

### Phase 1에서 다루지 않는 것 (Phase 2·3에서 다룸)

- ❌ 추천어 생성 (ghost suggestion)
- ❌ Conditional Edge / Router 노드
- ❌ Checkpointer / 세션 저장
- ❌ 음성 입력 (STT)
- ❌ Streamlit UI

---

## 🏗 아키텍처 (Phase 1)

### 노드 구성

| 노드                | 역할                               | LLM 사용 |
| ------------------- | ---------------------------------- | -------- |
| `setup_scenario`    | 시나리오 정보로 system prompt 빌드 | ❌       |
| `receive_input`     | 사용자 텍스트 입력 받기            | ❌       |
| `analyze_utterance` | 발화를 conversation_history에 누적 | ❌       |
| `generate_feedback` | 전체 대화를 LLM에 넘겨 피드백 생성 | ✅       |

### 흐름도

```
START
  │
  ▼
setup_scenario        (시나리오 → system_prompt 빌드)
  │
  ▼
receive_input  ◄─────┐  (터미널 input() 으로 한 줄 받기)
  │                  │
  ▼                  │
analyze_utterance    │  (history에 append)
  │                  │
  ├──────────────────┘  if not session_ended → 다시 receive_input
  │
  ▼  if session_ended
generate_feedback     (gpt-4o-mini로 전체 대화 분석)
  │
  ▼
END
```

### State 정의

```python
class ConversationState(TypedDict):
    # 시나리오 (setup 후 변경 없음)
    scenario: str
    system_prompt: str

    # 입력 (매 턴 갱신)
    raw_input: str
    session_ended: bool

    # 누적 (계속 쌓임)
    conversation_history: Annotated[List[dict], add]

    # 출력
    feedback: dict
```

---

## 📂 디렉토리 구조

```
tabby-english/
├── README.md
├── pyproject.toml              # uv용 의존성 정의
├── .env                        # API 키 (커밋 금지)
├── .gitignore
│
├── src/
│   ├── __init__.py
│   ├── state.py                # ConversationState 정의
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── setup_scenario.py
│   │   ├── receive_input.py
│   │   ├── analyze_utterance.py
│   │   └── generate_feedback.py
│   ├── graph.py                # 그래프 조립 (StateGraph)
│   └── prompts.py              # 시스템 프롬프트 템플릿
│
├── main.py                     # 진입점 (터미널 실행)
│
└── tests/
    └── test_phase1.py          # Phase 1 동작 검증
```

> Phase 2에서는 `src/nodes/`에 `generate_ghost.py`, `persist_session.py`가 추가되고 `src/router.py`가 새로 생깁니다. 기존 파일은 거의 그대로 유지됩니다.

---

## 🚀 시작하기

### 사전 요구사항

- Python 3.10 이상
- [uv](https://docs.astral.sh/uv/) 패키지 매니저
- OpenAI API 키

### 설치 (uv 사용)

```bash
git clone <repo-url>
cd tabby-english

# 가상환경 생성 + 의존성 설치 (한 번에)
uv sync
```

`uv sync`는 `pyproject.toml`을 읽어 `.venv/`를 만들고 의존성을 모두 설치합니다.
처음 실행 시 `uv.lock` 파일이 생성되어 의존성 버전이 고정됩니다.

### 환경 변수 설정

프로젝트 루트의 `.env` 파일에 OpenAI API 키를 입력합니다.

```env
OPENAI_API_KEY=sk-...
```

### 실행

```bash
uv run python main.py
```

`uv run`은 가상환경을 자동으로 활성화한 채로 명령을 실행합니다.
명시적으로 활성화하려면 `source .venv/bin/activate` 후 `python main.py`도 가능.

### 테스트 (LLM 호출 없음, 즉시 실행)

```bash
uv run python -m tests.test_phase1
```

---

## 💬 사용 예시

```
$ uv run python main.py

==================================================
  Tabby English — Phase 1
==================================================
시나리오를 입력하세요 (예: ordering at a cafe): ordering at a cafe

[시나리오: ordering at a cafe]
영어로 대화를 시작하세요. 종료하려면 'end'를 입력하세요.

You: Hi, I would like to order a coffee
You: Can I get a latte with oat milk?
You: How much is it?
You: end

──────────────────── 학습 피드백 ────────────────────
{
  "summary": "카페 주문 상황에서 자연스러운 표현을 사용했습니다.",
  "improvements": [
    {
      "original": "Can I get a latte with oat milk?",
      "suggestion": "Could I get a latte with oat milk, please?",
      "reason": "더 정중한 요청 표현"
    }
  ],
  "good_points": [
    "I would like to ~ 표현을 적절히 사용함"
  ]
}
──────────────────────────────────────────────────────
```

---

## ✅ Phase 1 완료 기준

다음 시나리오가 모두 통과하면 Phase 1 완료로 간주합니다.

1. 터미널에서 시나리오 입력 → 5턴 이상 영어 대화 → `end` 입력 시 피드백 출력
2. `conversation_history`에 모든 발화가 누적되어 있음 (LangSmith로 확인 가능)
3. `generate_feedback`이 구조화된 JSON 형태의 피드백 반환
4. 같은 코드를 다시 실행해도 동일하게 동작 (멱등성)

---

## 🔧 기술 스택

| 항목            | 사용 기술          | 비고                            |
| --------------- | ------------------ | ------------------------------- |
| 워크플로우 엔진 | LangGraph          | 학습 대상                       |
| LLM             | OpenAI gpt-4o-mini | Phase 1은 비용 낮은 모델로 검증 |
| 패키지 관리     | uv                 | 빠른 의존성 해석                |
| 디버깅          | LangSmith          | 그래프 실행 추적 (선택)         |
| 언어            | Python 3.10+       |                                 |

---

## 📚 참고 자료

- [LangGraph 공식 문서](https://langchain-ai.github.io/langgraph/)
- [LangGraph Quickstart](https://langchain-ai.github.io/langgraph/tutorials/introduction/)
- [uv 공식 문서](https://docs.astral.sh/uv/)
- [OpenAI API 문서](https://platform.openai.com/docs)

---

## 🗺 다음 단계 미리보기

### Phase 2: 추천어 + 영속성

- `generate_ghost` 노드 추가 (머뭇거림 감지 시 다음 표현 추천)
- `add_conditional_edges`로 router 도입
- `SqliteSaver`로 세션 저장·재개
- `persist_session` 노드로 학습 이력 누적

### Phase 3: Streamlit UI

- 시나리오 선택 / 채팅 인터페이스
- "💡 힌트" 버튼으로 ghost suggestion 호출
- 세션별 학습 기록 조회 화면

---

## 📝 라이선스

개인 학습 프로젝트
