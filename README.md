# 🐱 Tabby English

> IDE의 자동완성처럼, 영어로 말하다 막히는 순간 다음 표현을 띄워주는 영어 회화 코치

영어로 말하다 보면 한 단어가 떠오르지 않아 대화가 끊기는 순간이 있죠. **Tabby English**는 그 순간을 자동완성처럼 메워줍니다. AI 대화 상대(카페 직원, 면접관 등)와 영어로 자유롭게 대화하고, 막히면 💡 버튼 하나로 이어갈 표현 세 가지를 제안받으세요.

---

## 🎬 데모

> 스크린샷은 추후 추가 예정 (배포 후)

```
[사용자가 ☕ 카페 주문 카드 선택]
🤖 Partner: Hi! What can I get for you?

🧑 You: Hi, I would like[멈춤 → 💡 클릭]

💡 "I would like" 이어서 말하기
  ① I would like to order a latte
  ② I would like two iced americanos
  ③ I would like to see the menu first
```

---

## ✨ 핵심 기능

### 1. 시나리오 기반 양방향 대화

6가지 실생활 상황(카페 주문, 공항 체크인, 면접, 쇼핑, 식당 예약, 택시)에서 AI Partner와 영어로 대화합니다. 직접 시나리오를 입력할 수도 있어요.

### 2. 💡 추천어 (Ghost Suggestion)

미완성 문장 뒤에 이어갈 표현 세 가지를 제안합니다. 입력창에 `I would like` 까지만 친 상태에서도 회색(이미 친 부분) + 보라색(이어갈 부분)으로 시각적으로 합쳐 보여줘요.

추천 품질을 위해 LLM이 다음 두 가지 외부 정보를 참고합니다:

- **현재 시간대** — 아침에는 커피, 저녁에는 가벼운 디저트 등 맥락에 맞춤
- **학습자의 과거 약점** — 자주 틀린 표현 패턴을 피해 더 도움이 되는 추천 생성

### 3. 학습 피드백 + 이력 대시보드

`"end"` 입력으로 세션을 종료하면 전체 대화를 분석한 피드백을 받습니다(요약 / 개선점 / 잘한 점). 별도 페이지에서 누적 통계와 자주 지적된 표현 TOP 5를 시각화해서 시간을 들여 성장을 추적할 수 있어요.

---

## 🏗 아키텍처

LangGraph로 구성한 8개 노드 그래프 위에 Streamlit UI를 얹은 구조입니다.

```
                    ┌──────────┐
                    │  START   │
                    └────┬─────┘
                         ▼
                  ┌──────────────┐
                  │setup_scenario│
                  └──────┬───────┘
                         ▼
                  ┌──────────────┐
                  │receive_input │ ← signal 결정
                  └──────┬───────┘
                         ▼
                ╔════════════════╗
                ║  조건부 분기   ║
                ╚════╤═══════╤═══╝
       ┌─────────────┘   │       └──────────────┐
       │ utterance       │ silence              │ end_session
       ▼                 ▼                      ▼
   ┌────────────┐  ┌──────────────┐    ┌──────────────────┐
   │analyze_    │  │generate_ghost│    │generate_feedback │
   │utterance   │  │(도구 직접호출)│    │                  │
   └─────┬──────┘  └──────┬───────┘    └────────┬─────────┘
         ▼                ▼                     ▼
   ┌─────────────┐                       ┌──────────────┐
   │generate_ai_ │                       │persist_      │
   │response     │                       │session       │
   └─────┬───────┘                       └──────┬───────┘
         ▼                ▼                     ▼
                       END

   (Checkpointer가 모든 상태 전이를 thread_id 기준으로 자동 저장)
```

| 노드                   | 역할                                               |
| ---------------------- | -------------------------------------------------- |
| `setup_scenario`       | 시나리오 → system prompt 빌드                      |
| `receive_input`        | 입력 종류 판단 (utterance / silence / end_session) |
| `analyze_utterance`    | user 발화를 history에 누적                         |
| `generate_ai_response` | Partner의 영어 응답 생성                           |
| `generate_ghost`       | 추천 표현 3개 생성 (도구 직접 호출)                |
| `generate_feedback`    | 전체 대화 분석 후 학습 피드백                      |
| `persist_session`      | 학습 이력을 SQLite에 저장                          |

---

## 🚀 시작하기 (로컬)

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

프로젝트 루트에 `.env` 파일을 만들고 OpenAI API 키를 입력합니다.

```env
OPENAI_API_KEY=sk-...
```

### 실행

```bash
streamlit run app.py
```

브라우저가 자동으로 열리고 `http://localhost:8501`에서 앱이 실행됩니다.

### 테스트

```bash
uv run python -m tests.test_phase2
```

LangGraph 노드와 라우터의 단위 검증을 수행합니다. (LLM 호출 없이 즉시 통과)

---

## ☁️ Streamlit Cloud 배포

### 1. GitHub에 푸시

`.env`와 `data/` 폴더가 `.gitignore`에 포함되어 있는지 확인 후 푸시합니다.

```bash
git status   # .env, data/ 가 안 보이는지 확인
git push
```

### 2. Streamlit Cloud 연결

1. [share.streamlit.io](https://share.streamlit.io) 접속
2. GitHub 저장소 연결, 메인 파일은 `app.py`로 지정
3. **Settings → Secrets** 에 다음 내용 등록:

```toml
OPENAI_API_KEY = "sk-..."
```

4. **Deploy** 클릭

### 3. 배포 환경의 한계 인지

- **학습 이력 영속성**: Streamlit Cloud는 컨테이너 재시작 시 파일이 사라집니다. 학습 이력은 한 세션 동안만 보장돼요. 장기 추적이 필요하면 로컬에서 실행하세요.
- **API 비용**: OpenAI API 키가 공개 데모에 노출되면 비용이 빠르게 누적될 수 있으니, 가능하면 [사용량 제한](https://platform.openai.com/account/limits)을 설정해두세요.

---

## 📂 디렉토리 구조

```
tabby-english/
├── app.py                      # Streamlit 진입점
├── pages/
│   └── 1_📊_학습_이력.py        # 학습 이력 대시보드 페이지
│
├── src/                        # LangGraph 엔진 (백엔드)
│   ├── state.py
│   ├── prompts.py
│   ├── graph.py
│   ├── nodes/
│   │   ├── setup_scenario.py
│   │   ├── receive_input.py
│   │   ├── analyze_utterance.py
│   │   ├── generate_ai_response.py
│   │   ├── generate_ghost.py
│   │   ├── generate_feedback.py
│   │   └── persist_session.py
│   └── tools/
│       ├── time_tool.py
│       └── weak_points_tool.py
│
├── ui/                         # Streamlit UI 컴포넌트
│   ├── scenario_picker.py
│   ├── ghost_panel.py
│   └── feedback_view.py
│
├── tests/
│   └── test_phase2.py
│
├── .streamlit/
│   ├── config.toml             # 테마 설정
│   └── secrets.toml.example    # Secrets 템플릿
│
├── requirements.txt            # Streamlit Cloud용
├── pyproject.toml              # uv용
└── README.md
```

---

## 🔧 기술 스택

| 영역            | 사용 기술             |
| --------------- | --------------------- |
| 워크플로우 엔진 | LangGraph             |
| LLM             | OpenAI gpt-4o-mini    |
| UI              | Streamlit             |
| 영속성          | SqliteSaver + sqlite3 |
| 패키지 관리     | uv                    |
| 배포            | Streamlit Cloud       |

---

## 📚 학습한 LangGraph 개념

이 프로젝트는 LangGraph 학습 목적으로 진행되었습니다. 적용한 개념들:

- **State (TypedDict)** — 노드들이 공유하는 자료 구조
- **누적 필드 (`Annotated[List, add]`)** — append 시맨틱
- **Node** — 단일 책임 함수, 부분 업데이트 반환
- **일반 Edge / Conditional Edge** — 무조건 vs 상태 기반 분기
- **Tool 정의 (`@tool` 데코레이터)** — 외부 함수를 LLM 호출 가능 형태로
- **노드 내부 직접 도구 호출 패턴** — ReAct 순환 없이 단일 응답 사이클로 단순화
- **Checkpointer (SqliteSaver)** — 모든 상태 전이 자동 저장
- **thread_id** — 사용자/세션 단위로 대화 분리
- **URL 기반 세션 영속성** — Streamlit 새로고침에도 대화 유지

---

## 🗺 로드맵

- ✅ **Phase 1** — LangGraph 기본 (양방향 대화 + 피드백)
- ✅ **Phase 2** — 조건부 분기 + 도구 + Checkpointer
- ✅ **Phase 3** — Streamlit UI + 시각적 대시보드 + 배포
- ⏳ **Phase 4** — 음성 입력 + 진짜 ghost text (브라우저 안 회색 자동완성)

Phase 4에서는 Web Speech API와 커스텀 컴포넌트로 "말하다가 멈추면 화면에 다음 표현이 희미하게 떠오르는" 진짜 자동완성 경험을 구현할 예정입니다.

---

## 📝 라이선스

개인 학습 프로젝트
