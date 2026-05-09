# Tabby English

> IDE의 자동완성처럼, 영어로 말하다 막히는 순간 다음 표현을 띄워주는 회화 코칭 에이전트

LangGraph로 구현하는 영어회화 학습용 AI 에이전트입니다. AI 대화 상대(카페 직원, 면접관 등)와 양방향 영어 대화를 진행하고, 머뭇거릴 때 다음 표현을 추천받으며, 대화 종료 후 학습 피드백을 받습니다.

---

## 📍 프로젝트 단계 (Roadmap)

LangGraph 학습이 주 목적이며, 3단계로 점진적으로 구현합니다.

| 단계        | 핵심 목표                                    | 상태    |
| ----------- | -------------------------------------------- | ------- |
| **Phase 1** | LangGraph 뼈대 + 양방향 대화 + 피드백 생성   | ✅ 완료 |
| **Phase 2** | Conditional edges + Tool 사용 + Checkpointer | ✅ 완료 |
| **Phase 3** | Streamlit UI 통합                            | ⏳ 예정 |

---

## 🏗 그래프 구조

### 흐름도

```
                              ┌──────────┐
                              │  START   │
                              └────┬─────┘
                                   ▼
                          ┌────────────────┐
                          │ setup_scenario │  시나리오 → system prompt
                          └────────┬───────┘
                                   ▼
                          ┌────────────────┐
                          │ receive_input  │  입력을 보고 signal 결정
                          └────────┬───────┘
                                   ▼
                          ╔════════════════╗
                          ║   조건부 분기   ║  ← 점선
                          ╚════╤═══════╤═══╝
                ┌──────────────┘       │            └──────────────┐
                │ utterance            │ silence                   │ end_session
                ▼                      ▼                           ▼
      ┌──────────────────┐    ┌────────────────┐         ┌───────────────────┐
      │analyze_utterance │    │ generate_ghost │◄──┐     │ generate_feedback │
      └────────┬─────────┘    └────────┬───────┘   │     └─────────┬─────────┘
               ▼                       │           │               ▼
      ┌────────────────────┐           ▼           │     ┌───────────────────┐
      │generate_ai_response│      ╔═════════╗      │     │  persist_session  │
      └────────┬───────────┘      ║조건부 분기║     │     └─────────┬─────────┘
               │                  ╚════╤════╝      │               │
               │              tool 호출 │  완료     │               │
               │                       ▼           │               │
               │              ┌────────────────┐   │               │
               │              │     tools      │───┘               │
               │              └────────────────┘                   │
               │                                                   │
               └────────────────┐                ┌─────────────────┘
                                ▼                ▼
                              ┌──────────┐
                              │   END    │
                              └──────────┘
```

### LangGraph 표시 규칙

LangGraph가 자동 생성하는 시각화에서:

- **실선** = 일반 엣지 (`add_edge`로 등록, 무조건 다음 노드로 이동)
- **점선** = 조건부 엣지 (`add_conditional_edges`로 등록, State 값에 따라 분기)

---

## 📋 노드 명세

### 핵심 개념: 노드는 무엇을 하는가

각 노드는 **State(여행 가방)를 받아서, 변경된 부분만 반환**하는 함수입니다. 예를 들어 `analyze_utterance` 노드가 발화 하나를 history에 추가하면, 전체 State를 다시 만들지 않고 `{"conversation_history": [새_발화]}`만 반환합니다.

### 노드별 상세 설명

| 노드                   | 역할                                       | LLM | 도구 |
| ---------------------- | ------------------------------------------ | --- | ---- |
| `setup_scenario`       | 시나리오 문자열로 LLM용 system prompt 빌드 | ❌  | ❌   |
| `receive_input`        | 입력 내용을 보고 signal 종류 결정          | ❌  | ❌   |
| `analyze_utterance`    | user 발화를 conversation_history에 누적    | ❌  | ❌   |
| `generate_ai_response` | AI Partner 역할로 영어 응답 생성           | ✅  | ❌   |
| `generate_ghost`       | 머뭇거림 시 다음 표현 3개 추천             | ✅  | ✅   |
| `tools`                | LLM이 호출한 도구를 실행 (ToolNode)        | ❌  | ✅   |
| `generate_feedback`    | 전체 대화 분석 후 학습 피드백 JSON         | ✅  | ❌   |
| `persist_session`      | 학습 세션을 SQLite에 영구 저장             | ❌  | ❌   |

### 각 노드가 State에 끼치는 영향

| 노드                   | 읽는 필드                                      | 쓰는 필드                                           |
| ---------------------- | ---------------------------------------------- | --------------------------------------------------- |
| `setup_scenario`       | `scenario`                                     | `system_prompt`                                     |
| `receive_input`        | `raw_input`                                    | `input_signal`                                      |
| `analyze_utterance`    | `raw_input`                                    | `conversation_history` (append)                     |
| `generate_ai_response` | `conversation_history`, `scenario`             | `conversation_history` (append), `last_ai_response` |
| `generate_ghost`       | `conversation_history`, `scenario`, `messages` | `messages` 또는 `ghost_suggestions`                 |
| `tools`                | `messages`                                     | `messages` (append)                                 |
| `generate_feedback`    | `conversation_history`, `scenario`             | `feedback`                                          |
| `persist_session`      | `conversation_history`, `scenario`, `feedback` | (DB 저장, State 변경 없음)                          |

---

## 🔀 엣지 명세

| 출발                   | 도착                   | 종류       | 조건                            |
| ---------------------- | ---------------------- | ---------- | ------------------------------- |
| `START`                | `setup_scenario`       | 일반       | —                               |
| `setup_scenario`       | `receive_input`        | 일반       | —                               |
| `receive_input`        | `analyze_utterance`    | **조건부** | `input_signal == "utterance"`   |
| `receive_input`        | `generate_ghost`       | **조건부** | `input_signal == "silence"`     |
| `receive_input`        | `generate_feedback`    | **조건부** | `input_signal == "end_session"` |
| `analyze_utterance`    | `generate_ai_response` | 일반       | —                               |
| `generate_ai_response` | `END`                  | 일반       | 한 턴 종료                      |
| `generate_ghost`       | `tools`                | **조건부** | LLM이 도구 호출함               |
| `generate_ghost`       | `END`                  | **조건부** | 추천어 생성 완료                |
| `tools`                | `generate_ghost`       | 일반       | 도구 결과를 들고 LLM에 복귀     |
| `generate_feedback`    | `persist_session`      | 일반       | —                               |
| `persist_session`      | `END`                  | 일반       | 세션 종료                       |

---

## 🛠 도구 (Tools) 명세

### 도구는 왜 필요한가

**LLM이 자체적으로 알 수 없는 정보**를 외부에서 가져오기 위함입니다. LLM이 이미 아는 정보를 도구로 묻는 것은 의미가 없으므로, 두 도구 모두 LLM이 _원리적으로 알 수 없는_ 영역을 담당합니다.

| 도구                   | 반환                                | LLM이 모르는 이유                           |
| ---------------------- | ----------------------------------- | ------------------------------------------- |
| `get_time_of_day`      | `morning` / `afternoon` / `evening` | LLM은 학습 데이터 cutoff 이후의 시간을 모름 |
| `get_user_weak_points` | 과거 자주 지적된 개선점 목록        | LLM은 다른 세션의 데이터를 모름             |

### 동작 예시

머뭇거림(`""`) 입력 시 LLM의 추론은 다음과 같이 흘러갑니다:

> "사용자에게 다음 표현을 추천해야 한다. 시간대를 모르니 `get_time_of_day`를 부르자. 사용자가 자주 틀리는 패턴도 모르니 `get_user_weak_points`도 부르자."

→ 두 도구가 호출되고 → 결과를 받아 → "지금이 morning이고, 사용자가 'I want to' 대신 'I would like to'를 자주 까먹으니, 이번에는 'I would like a latte'를 추천하자" → 최종 답변 생성.

이 흐름이 **ReAct 패턴**(Reasoning + Acting)이며, 에이전트의 가장 기본적인 동작 원리입니다.

---

## 📦 State 구조

```python
class ConversationState(TypedDict):
    # 시나리오 (한 번 설정 후 유지)
    scenario: str
    system_prompt: str

    # 입력 (매 턴 갱신)
    raw_input: str
    input_signal: Literal["utterance", "silence", "end_session"]

    # 누적 (Annotated[List, add]로 자동 append)
    conversation_history: List[Utterance]
    messages: List[BaseMessage]   # generate_ghost ↔ tools 메시지 채널

    # 매 턴의 결과
    last_ai_response: str
    ghost_suggestions: List[str]

    # 종료 시
    feedback: Feedback
```

`Annotated[List, add]`는 "덮어쓰지 말고 append하라"는 LangGraph 패턴입니다. 노드가 `[새_항목]`을 반환하면 기존 리스트 뒤에 자동 추가됩니다.

---

## 🔁 입력별 흐름 가이드

> 이 섹션은 코드를 보지 않고도 어떤 노드들이 어떤 순서로 실행되는지 이해할 수 있도록 작성되었습니다.

### 케이스 1: 영어 문장 입력 (예: `"Hi, I'd like a coffee"`)

```
START
  → setup_scenario       (system prompt 빌드)
  → receive_input        (signal = "utterance")
  → analyze_utterance    (history에 user 발화 추가)
  → generate_ai_response (Partner의 영어 응답 생성, history에 추가)
  → END
```

**결과**: `state["last_ai_response"]`에 Partner 응답이 들어 있음.

### 케이스 2: 빈 문자열 입력 (`""`) — 머뭇거림

LLM이 도구를 호출하지 않고 바로 답하는 경우:

```
START
  → setup_scenario
  → receive_input        (signal = "silence")
  → generate_ghost       (LLM 호출 → 도구 없이 추천어 생성)
  → END
```

LLM이 도구를 호출하는 경우 (ReAct 순환):

```
START
  → setup_scenario
  → receive_input        (signal = "silence")
  → generate_ghost       (LLM 1차 호출 → 도구 사용 결정, messages에 누적)
  → tools                (도구 실행, 결과를 messages에 누적)
  → generate_ghost       (LLM 2차 호출 → 도구 결과를 보고 최종 답변)
  → END
```

도구가 여러 번 필요하면 `generate_ghost ↔ tools`를 N번 왕복할 수 있습니다.

**결과**: `state["ghost_suggestions"]`에 추천 표현 3개.

### 케이스 3: `"end"` 입력 — 세션 종료

```
START
  → setup_scenario
  → receive_input        (signal = "end_session")
  → generate_feedback    (LLM이 전체 대화 분석)
  → persist_session      (SQLite에 학습 세션 저장)
  → END
```

**결과**: `state["feedback"]`에 구조화된 피드백, `data/sessions.db`에 한 행 추가.

---

## ❓ 자주 묻는 질문

### Q1. 왜 `setup_scenario`는 매 턴마다 실행되나요?

`app.invoke()` 한 번이 그래프 한 사이클 통과입니다. 매 턴이 START에서 다시 시작하므로 모든 노드가 다시 실행돼요.

다만 `setup_scenario`는 LLM 호출이 없는 단순 문자열 조립이라 비용이 거의 0입니다. 또 `state["scenario"]`는 Checkpointer 덕에 이전 호출의 값이 자동 복원되므로 항상 같은 결과를 만듭니다 (멱등성).

### Q2. Checkpointer는 정확히 무엇을 저장하나요?

`SqliteSaver`가 **매 노드 실행 후의 State 전체**를 `data/checkpoints.db`에 저장합니다. `thread_id`를 키로 사용해서, 같은 thread_id로 invoke하면 이전 State가 자동 복원됩니다.

`persist_session` 노드의 SQLite 저장과는 별개입니다:

- **Checkpointer (`checkpoints.db`)**: 그래프 내부 동작용. LangGraph가 자동 관리.
- **persist_session (`sessions.db`)**: 사용자가 보기 좋은 학습 이력. 우리가 직접 설계.

### Q3. `messages` 필드는 왜 따로 있나요?

`conversation_history`는 사용자와 AI Partner 사이의 대화 기록이고, `messages`는 `generate_ghost` 노드와 `tools` 노드 사이의 메시지 교환 채널입니다. 용도가 다르므로 분리되어 있습니다.

`messages`에는 다음이 누적됩니다:

- `HumanMessage` — generate_ghost가 LLM에 보낸 prompt
- `AIMessage(tool_calls=[...])` — LLM이 도구 호출을 결정한 응답
- `ToolMessage` — `tools` 노드가 실행한 도구 결과

이건 LangGraph의 `ToolNode`가 표준으로 사용하는 형식입니다.

### Q4. 도구가 정말 호출되는 모습을 보려면?

빈 문자열(`""`)을 입력해 머뭇거림을 시뮬레이션하면 `generate_ghost`가 실행되고, LLM이 두 도구 중 하나 이상을 호출할 가능성이 높습니다. 학습 이력이 쌓일수록 `get_user_weak_points`가 더 자주 호출됩니다.

LangSmith를 연결하면 실제로 LLM이 어떤 도구를 호출했는지 시각적으로 볼 수 있습니다.

### Q5. 새로운 시나리오로 다시 시작하려면?

`main.ipynb`의 **세션 초기화 셀을 다시 실행**하면 새 `thread_id`가 생성됩니다. Checkpointer는 thread_id별로 분리되어 있으므로, 새 thread_id로 시작하면 이전 대화와 완전히 독립적인 새 세션이 됩니다.

---

## 📂 디렉토리 구조

```
tabby-english/
├── README.md
├── pyproject.toml              # uv용 의존성 정의
├── .env                        # OPENAI_API_KEY (커밋 금지)
├── .gitignore
│
├── main.ipynb                  # Jupyter 진입점
│
├── src/
│   ├── state.py                # ConversationState 타입 정의
│   ├── prompts.py              # AI Partner / Ghost / Feedback 프롬프트
│   ├── graph.py                # StateGraph 조립 + Checkpointer 통합
│   ├── nodes/
│   │   ├── setup_scenario.py
│   │   ├── receive_input.py
│   │   ├── analyze_utterance.py
│   │   ├── generate_ai_response.py
│   │   ├── generate_ghost.py
│   │   ├── generate_feedback.py
│   │   └── persist_session.py
│   └── tools/
│       ├── time_tool.py            # get_time_of_day
│       └── weak_points_tool.py     # get_user_weak_points
│
├── tests/
│   └── test_phase2.py          # 노드·도구·라우터 검증
│
└── data/                       # 첫 실행 시 자동 생성, gitignore됨
    ├── checkpoints.db          # Checkpointer (그래프 상태)
    └── sessions.db             # persist_session (학습 이력)
```

---

## 🚀 시작하기

### 사전 요구사항

- Python 3.10 이상
- [uv](https://docs.astral.sh/uv/) 패키지 매니저
- OpenAI API 키

### 설치

```bash
git clone <repo-url>
cd tabby-english
uv sync
```

### 환경 변수

`.env` 파일에 OpenAI API 키를 입력합니다.

```env
OPENAI_API_KEY=sk-...
```

### 테스트 (LLM 호출 없음, 즉시 통과)

```bash
uv run python -m tests.test_phase2
```

### 메인 실행

`main.ipynb`를 프로젝트 루트에서 열고 셀을 순서대로 실행합니다.

---

## 💬 사용 예시

```
[셀: 대화]
user_input = "Hi, I would like to order a coffee"
→ You:     Hi, I would like to order a coffee
  Partner: Sure! What kind of coffee would you like?

[user_input = ""]
→ 💡 추천 표현:
     • a hot americano please
     • the breakfast set
     • something with oat milk

[user_input = "I'll have an iced latte"]
→ You:     I'll have an iced latte
  Partner: Got it. What size?

[user_input = "end"]
→ 세션이 종료되어 피드백이 생성되고 DB에 저장되었습니다.
  {
    "summary": "...",
    "improvements": [...],
    "good_points": [...]
  }
```

---

## 🔧 기술 스택

| 항목            | 사용 기술                                        |
| --------------- | ------------------------------------------------ |
| 워크플로우 엔진 | LangGraph                                        |
| LLM             | OpenAI gpt-4o-mini                               |
| 영속성          | SqliteSaver (Checkpointer) + sqlite3 (학습 이력) |
| 패키지 관리     | uv                                               |
| 타입 검사       | mypy                                             |
| 진입점          | Jupyter Notebook                                 |

---

## 📚 학습한 LangGraph 개념

- **State** — TypedDict 기반의 공유 상태
- **누적 필드** — `Annotated[List, add]` 패턴
- **Node** — 단일 책임 함수, 부분 업데이트 반환
- **일반 Edge** — `add_edge`로 무조건 다음 노드
- **Conditional Edge** — `add_conditional_edges`로 상태 기반 분기
- **Tool 정의** — `@tool` 데코레이터
- **Tool Binding** — `llm.bind_tools(...)`로 LLM이 도구를 인식
- **ToolNode** — LangGraph prebuilt로 도구 실행 자동화
- **ReAct 패턴** — LLM ↔ ToolNode 순환 (Reasoning + Acting)
- **Checkpointer** — `SqliteSaver`로 모든 상태 전이 자동 저장
- **thread_id** — 사용자/세션 단위로 대화 분리

---

## 🗺 다음 단계: Phase 3

- Streamlit으로 채팅 인터페이스 구현
- 시나리오 선택 UI
- 💡 힌트 버튼으로 ghost suggestion 호출
- 세션별 학습 기록 조회 화면

---

## 📝 라이선스

개인 학습 프로젝트
