# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
# pip install fastapi

from pydantic import BaseModel
# pip install pydantic

from dotenv import load_dotenv
# pip install python-dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains import create_history_aware_retriever
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
# pip install langchain
# pip install langchain-openai
# pip install langchain-community
# pip install langchain-core
# pip install langchain-classic
# pip install openai
# pip install chromadb

import json

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
def read_root():
    return {"status": "FastAPI Server is running with ChromaDB Vector Store!"}

# 학생들에게 보여줄 가상의 교내 정보 데이터셋 (원시 데이터)
sample_documents = [
    Document(
        page_content="FastAPI 실습실은 공학관 301호에 있으며, 이용 시간은 평일 오전 9시부터 오후 6시까지입니다.",
        metadata={"source": "classroom_info"},
    ),
    Document(
        page_content="리액트(React) 프로젝트 과제 제출 기한은 2026년 7월 15일 자정까지이며, 기한 엄수 바랍니다.",
        metadata={"source": "homework_info"},
    ),
    Document(
        page_content="이번 IT 교육 과정의 담당 교수님은 양현수 교수님이며, 이메일은 yang@example.com 입니다.",
        metadata={"source": "professor_info"},
    ),
    Document(
        page_content="크로마DB(ChromaDB)는 오픈소스 벡터 데이터베이스로, 빠르고 간편하게 로컬 환경에 구축할 수 있는 장점이 있습니다.",
        metadata={"source": "db_info"},
    ),
]

# 텍스트를 벡터로 변환할 임베딩 모델 초기화
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 크로마DB 초기화 및 데이터 저장 (로컬./chroma_db 폴더에 저장)
# 서버가 켜질 때 고유한 텍스트들을 임베딩하여 DB에 채워 넣는다.
persistent_directory = "./chroma_db"
vector_store = Chroma.from_documents(
    documents=sample_documents,
    embedding=embeddings,
    persist_directory=persistent_directory
)

# 검색기(Retriever) 설정: 가장 유사한 문서 2개를 가져오도록 설정
retriever = vector_store.as_retriever(search_kwargs={"k": 2})

# RAG 체인 + 대화 메모리 통합
session_store = {}

def get_session_history(session_id: str):
    if session_id not in session_store:
        session_store[session_id] = ChatMessageHistory()
    return session_store[session_id]

# 최적화를 위해 실시간 스트리밍에 적합한 설정 적용
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, streaming=True)

# 대화 기록을 반영하여 질문을 재구성하는 프롬프트
contextualize_q_system_prompt = (
    "이전 대화 기록과 사용자의 최신 질문이 주어집니다. "
    "최신 질문이 이전 대화의 문맥에 의존하고 있다면, 대화 기록 없이도 이해할 수 있는 독립적인 질문으로 재구성하세요. "
    "질문에 답하지 말고, 필요한 경우에만 질문을 재구성하고 그렇지 않으면 그대로 반환하세요."
)
contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("history"),
    ("human", "{input}"),
])

# 질문 재구성하기 (History Aware Retriever)
history_aware_retriever = create_history_aware_retriever(
    llm, retriever, contextualize_q_prompt
)

# 검색된 문서를 바탕으로 답변을 생성하는 프롬프트
qa_system_prompt = (
    "당신은 친절하고 전문적인 IT 교육 도우미 챗봇입니다. "
    "학생들이 프로그래밍 개념을 쉽게 이해할 수 있도록 명확하고 간결하게 한국어로 설명해주세요. "
    "다음 제공된 문맥(context)을 사용하여 질문에 답하세요. "
    "만약 문맥에서 답을 찾을 수 없다면, 모른다고 말하고 지어내지 마세요.\n\n"
    "{context}"
)
qa_prompt = ChatPromptTemplate.from_messages([
    ("system", qa_system_prompt),
    MessagesPlaceholder("history"),
    ("human", "{input}"),
])

# 문서 결합 체인 및 최종 RAG 체인 생성
question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

# 대화 메모리를 RAG 체인에 연결
conversation_with_rag_memory = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
    output_messages_key="answer",
)

# API 요청/응답 규격 정의 및 엔드포인트
class MessageRequest(BaseModel):
    message: str

class SearchRequest(BaseModel):
    query: str

# 타자 치는 효과(Streaming)를 위한 전용 엔드포인트
@app.post("/api/chat/stream")
async def chat_stream_endpoint(req: MessageRequest):
    async def event_generator():
        try:
            async for event in conversation_with_rag_memory.astream_events(
                {"input": req.message},
                version="v1",
                config={
                    "configurable": {
                        "session_id": "student_1"
                    }
                }
            ):
                # 디버깅용 (정상 동작 확인 후 삭제 가능)
                print(event)

                if event["event"] == "on_chat_model_stream":

                    chunk = event["data"]["chunk"]

                    if hasattr(chunk, "content") and chunk.content:

                        data_json = json.dumps(
                            {"text": chunk.content},
                            ensure_ascii=False
                        )

                        yield f"data: {data_json}\n\n"

            # 응답 완료 신호
            yield "data: [DONE]\n\n"

        except Exception as e:
            error_json = json.dumps(
                {"error": f"오류가 발생했습니다: {str(e)}"},
                ensure_ascii=False
            )
            yield f"data: {error_json}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

# 채팅 엔드포인트에 RAG 적용
@app.post("/api/chat")
async def chat_endpoint(req: MessageRequest):
    user_message = req.message
    try:
        # RAG 파이프라인 실행
        response = conversation_with_rag_memory.invoke(
            {"input": user_message},
            config={"configurable": {"session_id": "student_1"}}
        )
        
        bot_reply = response["answer"]
        
        # 답변 생성에 사용된 참고 문서(출처) 추출
        source_docs = response.get("context", [])
        sources = list(set([doc.metadata.get("source", "unknown") for doc in source_docs]))

        return {
            "reply": bot_reply,
            "sources": sources
        }
    except Exception as e:
        return {"reply": f"오류가 발생했습니다: {str(e)}", "sources": []}

# 크로마 DB 유사도 검색 전용 엔드포인트
@app.post("/api/search")
async def search_endpoint(req: SearchRequest):
    student_query = req.query
    try:
        results = vector_store.similarity_search(student_query, k=2)
        search_results = [
            {"content": doc.page_content, "metadata": doc.metadata} 
            for doc in results
        ]
        return {"status": "success", "results": search_results}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}