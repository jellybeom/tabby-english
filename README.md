# 🐱 Tabby English

> IDE의 자동완성처럼, 영어로 말하다 막히는 순간 다음 표현을 띄워주는 영어 회화 코치

영어로 말하다 보면 한 단어가 떠오르지 않아 대화가 끊기는 순간이 있죠. **Tabby English**는 그 순간을 자동완성처럼 메워줍니다.

AI 대화 상대와 영어로 자유롭게 대화하며, 막히면 다음 두 가지 방식으로 도움을 받을 수 있어요:

- **키보드 모드**: 💡 버튼 클릭으로 추천 표현 3개를 칩 형태로 받기
- **음성 모드**: 마이크로 영어를 말하다 멈추면, 입력창 안에 다음 표현이 회색으로 자동으로 떠오르고 Tab 키로 채택

---

## 🎬 데모

> 스크린샷은 배포 후 추가 예정

```
[사용자가 ☕ 카페 주문 카드 선택]
[입력 모드 선택 → 🎤 음성으로 시작]
[마이크 버튼 ON]

🧑 You (마이크):  "Hi, I would like..."
                                  [잠시 침묵]
입력창 안:        I would like to order a latte
                  [── 검정 ──][──── 회색 ghost ────]
                            ↑ Tab 누르면 채택

🤖 Partner: Sure! What size would you like?

🧑 You (마이크): "Medium please."
🤖 Partner: Anything else?
...
🧑 You: end
[세션 종료 → 학습 피드백 화면]
```

---

## ✨ 핵심 기능

### 1. 시나리오 기반 양방향 대화

6가지 실생활 상황(카페 주문, 공항 체크인, 면접, 쇼핑, 식당 예약, 택시)에서 AI Partner와 영어로 대화합니다. 직접 시나리오를 입력할 수도 있어요.

### 2. 💡 추천어 (Ghost Suggestion)

미완성 문장 뒤에 이어갈 표현 세 가지를 제안합니다. 입력창에 `I would like` 까지만 친 상태에서도 회색(이미 친 부분) + 보라색(이어갈 부분)으로 시각적으로 합쳐 보여줘요.

LLM이 다음 두 가지 외부 정보를 참고하여 추천 품질을 높입니다:

- **현재 시간대** — 아침에는 커피, 저녁에는 가벼운 디저트 등 맥락에 맞춤
- **학습자의 과거 약점** — 자주 틀린 표현 패턴을 피해 더 도움이 되는 추천 생성

### 3. 🎤 음성 입력 + 진짜 Ghost Text

Web Speech API로 영어를 말하고, 입력창 안에 자동완성처럼 다음 표현이 회색으로 떠오릅니다. Tab 키로 채택하거나 계속 말하면 사라져요.

세 가지 트리거가 자연스럽게 작동:

- 키보드 입력 → 3초 무입력 시 추천
- 음성 입력 → 2.5초 무음 시 추천 (즉시 발동)
- Tab 키 → 추천 채택

### 4. 학습 피드백 + 이력 대시보드

`"end"` 입력으로 세션을 종료하면 전체 대화를 분석한 피드백을 받습니다(요약 / 개선점 / 잘한 점). 별도 페이지에서 누적 통계와 자주 지적된 표현 TOP 5를 시각화해서 시간을 들여 성장을 추적할 수 있어요.

---

## 🏗 아키텍처

LangGraph로 구성한 7개 노드 그래프 위에 Streamlit UI를 얹고, 음성 입력을 위한 커스텀 컴포넌트(HTML + Vanilla JS)를 추가한 구조입니다.

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
| `generate_ghost`       | 추천 표현 3개 생성 (시간대, 약점 정보 활용)        |
| `generate_feedback`    | 전체 대화 분석 후 학습 피드백                      |
| `persist_session`      | 학습 이력을 SQLite에 저장                          |

### 입력 모드별 UI 분기

```
시나리오 선택 (카드 갤러리)
       ↓
입력 모드 선택 (⌨️ 키보드 / 🎤 음성)
       ↓
   ┌───┴───┐
   ↓       ↓
키보드     음성
   ↓       ↓
💡 칩     ghost_input 컴포넌트
방식      (contenteditable + Web Speech API)
```

음성 모드는 별도 커스텀 컴포넌트(`components/ghost_input/`)에서 마이크 권한 처리와 ghost text 렌더링을 담당합니다.

---

## 🚀 시작하기 (로컬)

### 사전 요구사항

- Python 3.10 이상
- [uv](https://docs.astral.sh/uv/) 패키지 매니저
- OpenAI API 키
- **음성 모드 사용 시**: Chrome 또는 Edge 브라우저 + 마이크

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

### 음성 모드를 처음 사용할 때

1. 마이크 버튼(🎤) 클릭 시 브라우저가 마이크 권한을 요청합니다 → **허용** 선택
2. 영어로 천천히, 또박또박 말해보세요
3. 잠시 멈추면 회색 ghost text가 떠오릅니다 → Tab으로 채택
4. 인식 결과가 다르게 나오면 입력창에서 키보드로 직접 수정 가능

### 테스트

```bash
uv run python -m tests.test_nodes
```

LangGraph 노드와 라우터의 단위 검증을 수행합니다.

---

## ☁️ Streamlit Cloud 배포

### 1. GitHub에 푸시

`.env`, `data/`, `secrets.toml`이 `.gitignore`에 포함되어 있는지 확인.

```bash
git status   # 위 파일들이 안 보이는지 확인
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

### 3. 음성 모드와 HTTPS

Streamlit Cloud는 자동으로 HTTPS를 제공하므로 **음성 인식이 로컬보다 더 안정적으로 작동**합니다. Web Speech API는 보안 컨텍스트(HTTPS 또는 localhost)에서만 동작하므로 배포 환경이 오히려 유리해요.

### 4. 배포 환경의 한계 인지

- **학습 이력 영속성**: Streamlit Cloud는 컨테이너 재시작 시 파일이 사라집니다. 학습 이력은 한 세션 동안만 보장돼요. 장기 추적이 필요하면 로컬에서 실행하세요.
- **API 비용**: OpenAI API 키가 공개 데모에 노출되면 비용이 빠르게 누적될 수 있으니, 가능하면 [사용량 제한](https://platform.openai.com/account/limits)을 설정해두세요.

---

## ⚠️ 알려진 한계

### Web Speech API

- **Chrome / Edge에서 가장 안정적**, Firefox는 부분 지원, Safari는 한정 지원
- 인터넷 연결 필요 (Google 음성 인식 서버 사용)
- 짧은 발화는 가끔 문맥적으로 보강되어 다른 단어가 인식될 수 있음 → 입력창에서 직접 수정 가능
- 마이크 권한 거부 시 자동으로 키보드 모드 fallback 안내

### LLM 추천 품질

- gpt-4o-mini 사용 — 비용 효율과 응답 속도의 균형
- 가끔 어색한 추천이 나올 수 있음. 프롬프트와 코드 후처리(`_dedupe_overlap`)로 단어 중복은 차단

---

## 📂 디렉토리 구조

```
tabby-english/
├── app.py                         # Streamlit 진입점 (시나리오/모드 분기)
├── pages/
│   └── 1_📊_학습_이력.py           # 학습 이력 대시보드 페이지
│
├── src/                           # LangGraph 엔진 (백엔드)
│   ├── state.py                   # ConversationState + InputMode 정의
│   ├── prompts.py
│   ├── graph.py
│   ├── nodes/                     # 7개 노드
│   └── tools/                     # 2개 도구 (시간, 약점 분석)
│
├── ui/                            # Streamlit UI 컴포넌트 (Python)
│   ├── scenario_picker.py
│   ├── input_mode_picker.py       # 키보드/음성 모드 선택
│   ├── ghost_panel.py
│   └── feedback_view.py
│
├── components/                    # 커스텀 Streamlit 컴포넌트 (HTML + JS)
│   └── ghost_input/
│       ├── __init__.py            # Python 래퍼
│       └── frontend/
│           ├── index.html         # contenteditable + Web Speech API
│           └── streamlit-component-lib.js
│
├── tests/
│   └── test_nodes.py
│
├── .streamlit/
│   ├── config.toml                # 테마 설정
│   └── secrets.toml.example       # Secrets 템플릿
│
├── requirements.txt               # Streamlit Cloud용
├── pyproject.toml                 # uv용
└── README.md
```

---

## 🔧 기술 스택

| 영역              | 사용 기술                             |
| ----------------- | ------------------------------------- |
| 워크플로우 엔진   | LangGraph                             |
| LLM               | OpenAI gpt-4o-mini                    |
| UI                | Streamlit                             |
| 음성 인식         | Web Speech API (브라우저 내장)        |
| 컴포넌트 frontend | HTML + Vanilla JavaScript (빌드 없음) |
| 영속성            | SqliteSaver + sqlite3                 |
| 패키지 관리       | uv                                    |
| 배포              | Streamlit Cloud                       |

---

## 📚 학습한 핵심 개념

이 프로젝트는 학습 목적으로 진행되었습니다. 적용한 개념들:

**LangGraph**

- State (TypedDict) — 노드들이 공유하는 자료 구조
- 누적 필드 (`Annotated[List, add]`) — append 시맨틱
- Node — 단일 책임 함수, 부분 업데이트 반환
- 일반 Edge / Conditional Edge — 무조건 vs 상태 기반 분기
- Tool 정의 (`@tool` 데코레이터) — 외부 함수를 LLM 호출 가능 형태로
- **노드 내부 직접 도구 호출 패턴** — ReAct 순환 없이 단일 응답 사이클로 단순화 (학습 중 옵션 A로 선회한 의사결정)
- Checkpointer (SqliteSaver) — 모든 상태 전이 자동 저장
- thread_id — 사용자/세션 단위로 대화 분리

**Streamlit 심화**

- `st.cache_resource`로 그래프 인스턴스 캐싱
- URL 기반 세션 영속성 (`st.query_params`)
- 위젯 생명주기 처리 (플래그 + rerun 패턴)
- 멀티페이지 앱 (`pages/`)
- **커스텀 컴포넌트** (`components.declare_component`)

**브라우저 측 JavaScript**

- iframe 안에서의 `postMessage` 통신
- `contenteditable` div로 입력창 직접 구현
- `beforeinput` 이벤트로 키 입력 가로채기
- 단일 데이터 흐름 (변수 → render 함수 → DOM)
- Web Speech API (`SpeechRecognition`) 활용
- 디바운싱 타이머 (3초/2.5초 무입력 감지)
- 메시지 객체 + nonce로 양방향 통신

---

## 🗺 로드맵

- ✅ **Phase 1** — LangGraph 기본 (양방향 대화 + 피드백)
- ✅ **Phase 2** — 조건부 분기 + 도구 + Checkpointer
- ✅ **Phase 3** — Streamlit UI + 시각적 대시보드 + 배포
- ✅ **Phase 4** — 음성 입력 + 진짜 ghost text (입력창 안 회색 자동완성)

---

## 📝 라이선스

개인 학습 프로젝트
