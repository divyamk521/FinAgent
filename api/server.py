from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

from agent import create_graph, invoke_graph
from config import config


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []

class ChatResponse(BaseModel):
    response: str
    model: str

def create_app() -> FastAPI:
    app = FastAPI(
        title="FinAgent API",
        description="AI-powered financial analyst REST API",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Activate LangSmith tracing at server startup
    config.setup_langsmith()

    # Compile graph once at startup
    graph = create_graph()

   

    # ── Routes 
    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "model": config.LLM_MODEL,
            "langsmith_tracing": config.LANGSMITH_TRACING,
            "langsmith_project": config.LANGSMITH_PROJECT if config.LANGSMITH_TRACING else None,
        }

    @app.post("/chat", response_model=ChatResponse)
    def chat(req: ChatRequest):
        if not config.GROQ_API_KEY:
            raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured.")

        # Rebuild message list from history
        messages = []
        for h in req.history:
            role = h.get("role", "user")
            content = h.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            else:
                messages.append(AIMessage(content=content))

        messages.append(HumanMessage(content=req.message))

        result = invoke_graph(
            graph,
            messages,
            run_name=f"api: {req.message[:60]}",
        )

        answer = ""
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                answer = msg.content
                break

        return ChatResponse(response=answer, model=config.LLM_MODEL)

    return app


# Allow `uvicorn api.server:app` directly
app = create_app()
