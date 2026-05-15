/**
 * Streamlit 컴포넌트 통신 라이브러리 (간소 버전).
 *
 * Streamlit 공식 라이브러리의 핵심 기능만 추출.
 * iframe 안에서 부모 Streamlit과 postMessage로 통신한다.
 *
 * 이 파일은 같은 폴더의 index.html에서 다음과 같이 로드:
 *   <script src="./streamlit-component-lib.js"></script>
 *
 * 그러면 window.Streamlit 전역 객체가 만들어진다.
 */
(function () {
  // 부모 창(Streamlit 앱)으로 메시지를 보내는 헬퍼
  function sendMessageToStreamlit(type, data) {
    window.parent.postMessage(
      { isStreamlitMessage: true, type: type, ...data },
      "*"
    );
  }

  // EventTarget을 상속받아 RENDER_EVENT를 dispatch할 수 있게 만든다
  const events = new EventTarget();

  // 부모(Streamlit)로부터 오는 메시지 수신
  window.addEventListener("message", function (event) {
    if (event.data.type === "streamlit:render") {
      const customEvent = new CustomEvent("streamlit:render", {
        detail: event.data,
      });
      events.dispatchEvent(customEvent);
    }
  });

  // window.Streamlit 전역 객체 노출
  window.Streamlit = {
    // 이벤트 리스너 등록용
    events: events,

    // 상수 — 이벤트 이름. 사용자가 'Streamlit.RENDER_EVENT'로 참조
    RENDER_EVENT: "streamlit:render",

    // 컴포넌트가 준비되었음을 부모에 알림
    setComponentReady: function () {
      sendMessageToStreamlit("streamlit:componentReady", { apiVersion: 1 });
    },

    // 컴포넌트의 값을 부모(Python)에 전달
    setComponentValue: function (value) {
      sendMessageToStreamlit("streamlit:setComponentValue", { value: value });
    },

    // iframe 높이 설정 (콘텐츠 잘림 방지)
    setFrameHeight: function (height) {
      sendMessageToStreamlit("streamlit:setFrameHeight", { height: height });
    },
  };
})();