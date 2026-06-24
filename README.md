### Streaming RAG Chatbot
FastAPI와 React를 활용한 LangChain · ChromaDB 기반 실시간 스트리밍 RAG 챗봇 프로젝트

### 프로젝트 소개
백엔드는 FastAPI를 사용하여 REST API 서버를 구축하고, 프론트엔드는 React(Vite)를 사용하여 사용자 인터페이스를 구현하였다. OpenAI API와 LangChain을 활용하여 사용자와 자연스러운 대화를 수행하며, ChromaDB 벡터 데이터베이스를 이용한 RAG(Retrieval-Augmented Generation) 기능을 제공한다.

또한 History-Aware Retriever를 적용하여 이전 대화 문맥을 고려한 검색이 가능하며, Streaming 응답 방식을 통해 AI가 답변을 생성하는 과정을 실시간으로 확인할 수 있다.

사용자의 질문은 임베딩(Embedding)을 통해 벡터로 변환되고, ChromaDB에서 관련 문서를 검색한 후 검색 결과를 기반으로 답변을 생성한다. 이를 통해 RAG 파이프라인과 벡터 검색 시스템의 동작 원리를 학습할 수 있다.

### 기술 스택
#### Backend
- Python
- FastAPI
- LangChain
- LangChain Classic
- OpenAI API
- ChromaDB
- OpenAI Embeddings
- Python-dotenv

#### Frontend
- React
- Vite
- JavaScript
- CSS

### 실행 방법
#### Backend
```bash
cd backend
uvicorn main:app --reload --port 8080
```

#### Frontend
```bash
cd frontend/product-app
npm install
npm run dev -- --port 3000
```

### 주요 기능
#### AI 챗봇
- OpenAI API 기반 자연어 대화
- LangChain Memory를 활용한 대화 기록 유지
- 이전 대화 문맥을 고려한 응답 생성
- FastAPI REST API 기반 채팅 서비스

#### RAG(Retrieval-Augmented Generation)
- OpenAI Embedding 모델을 활용한 텍스트 벡터화
- ChromaDB 벡터 데이터베이스 구축
- 유사도 기반 문서 검색
- 검색된 문서를 기반으로 답변 생성
- 답변 생성에 사용된 문서 출처(Source) 제공

#### History-Aware Retriever
- 이전 대화 기록을 활용한 질문 재구성
- 문맥 기반 검색 정확도 향상
- 후속 질문(Follow-up Question) 지원

#### Streaming 응답
- Server-Sent Events(SSE) 기반 실시간 응답
- ChatGPT와 유사한 타이핑 효과 구현
- 답변 생성 과정을 실시간으로 출력

#### 프론트엔드
- React 기반 사용자 인터페이스
- 실시간 채팅 기능
- 스트리밍 응답 출력
- API 기반 백엔드 연동

### 프로젝트 구조
```text
streaming-rag-chatbot
├── backend
│   ├── chroma_db
│   ├── main.py
│   └── requirements.txt
│
└── frontend
    └── product-app
        ├── src
        │   ├── App.jsx
        │   └── App.css
        └── package.json
```

### 프로젝트 목적
- FastAPI를 활용한 REST API 개발 학습
- React 기반 프론트엔드 구현
- OpenAI API를 활용한 LLM 서비스 개발
- LangChain Memory 기능 학습
- ChromaDB 벡터 데이터베이스 활용
- Embedding 개념 이해
- RAG(Retrieval-Augmented Generation) 구현
- History-Aware Retriever 활용
- Streaming 응답 처리 방식 학습
- 백엔드와 프론트엔드 연동 학습
- 실시간 AI 서비스 아키텍처 이해
