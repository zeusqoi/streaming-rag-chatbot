// App.jsx

import { useState } from 'react'
import './App.css'

function App() {
  const [inputText, setInputText] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false); // 로딩 및 중복 요청 방지 상태 추가

  const sendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    // 사용자 메시지 화면 추가
    const userMsg = inputText;
    setInputText("");
    setIsLoading(true);

    // 사용자의 질문과 동시에 봇의 답변이 적힐 '빈 상자'를 미리 만들어 둔다.
    setMessages((prev) => [
      ...prev, 
      { sender: "user", text: userMsg },
      { sender: "bot", text: "", sources: [] } // 텍스트가 실시간으로 채워질 영역
    ]);

    try {
      // FastAPI의 스트리밍 엔드포인트로 전송
      const response = await fetch("http://localhost:8080/api/chat/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: userMsg }),
      });

      // ReadableStream을 통해 들어오는 데이터 조각들을 읽어들임
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      while (true) {
        const { done, value } = await reader.read();
        
        // 스트림이 완전히 종료되면 루프 탈출
        if (done) break;

        // 넘어온 바이트 배열을 문자열로 디코딩 (SSE 포맷)
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.replace("data: ", "").trim();
            
            // 종료 신호를 받으면 스트리밍 중지
            if (dataStr === "[DONE]") {
              setIsLoading(false);
              return;
            }

            try {
              // JSON으로 안전하게 포장된 데이터를 풀어서 텍스트 추가
              const parsedData = JSON.parse(dataStr);

              if (parsedData.error) {
                console.error("서버 에러 응답:", parsedData.error);
                setIsLoading(false);
                return;
              }

              // 배열의 가장 마지막 메시지(봇의 빈 상자)에 글자를 계속 이어 붙임 (타이핑 효과)
              setMessages((prev) => {
                const newMessages = [...prev];
                const lastIndex = newMessages.length - 1;
                newMessages[lastIndex] = {
                  ...newMessages[lastIndex],
                  text: newMessages[lastIndex].text + parsedData.text
                };
                return newMessages;
              });

            } catch (err) {
              // JSON 파싱 에러 무시 (스트림 중간에 잘린 텍스트 조각일 수 있음)
              continue;
            }
          }
        }
      }
      
    } catch (error) {
      console.error("서버 통신 에러:", error);
      setMessages((prev) => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1].text = "서버와 연결할 수 없거나 스트리밍 중 오류가 발생했습니다.";
        return newMessages;
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: "500px", margin: "50px auto", fontFamily: "sans-serif" }}>
      <h2>최적화 RAG 챗봇 (Phase 6 - Streaming)</h2>
      
      {/* 채팅 내역 출력 영역 */}
      <div style={{ border: "1px solid #ccc", padding: "10px", height: "500px", overflowY: "auto", marginBottom: "10px", backgroundColor: "#f9f9f9" }}>
        {messages.map((msg, index) => (
          <div key={index} style={{ textAlign: msg.sender === "user" ? "right" : "left", margin: "15px 0" }}>
            <div style={{ 
              background: msg.sender === "user" ? "#d1e7dd" : "#ffffff", 
              border: msg.sender === "user" ? "none" : "1px solid #ddd",
              padding: "10px 14px", 
              borderRadius: "10px",
              display: "inline-block",
              maxWidth: "80%",
              boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
              textAlign: "left"
            }}>
              <div style={{ whiteSpace: "pre-wrap", lineHeight: "1.5" }}>
                {msg.text.length === 0 && msg.sender === "bot" ? "생성 중..." : msg.text}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 입력 및 전송 영역 */}
      <div style={{ display: "flex", gap: "10px" }}>
        <input 
          type="text" 
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="질문을 입력하세요."
          disabled={isLoading}
          style={{ flex: 1, padding: "12px", borderRadius: "5px", border: "1px solid #ccc" }}
        />
        <button 
          onClick={sendMessage} 
          disabled={isLoading}
          style={{ 
            padding: "10px 20px", 
            backgroundColor: isLoading ? "#6c757d" : "#0d6efd", 
            color: "white", 
            border: "none", 
            borderRadius: "5px", 
            cursor: isLoading ? "not-allowed" : "pointer" 
          }}
        >
          {isLoading ? "대기중" : "전송"}
        </button>
      </div>
    </div>
  );
}

export default App;