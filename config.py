import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class Config:
    
    GROQ_API_KEY: str       = os.environ.get("GROQ_API_KEY", "")
    FINLIGHT_API_KEY: str   = os.environ.get("FINLIGHT_API_KEY", "")

    # ── Optional ──────────────────────────────────────────────────────────────
#     JINA_API_KEY: Optional[str] = os.environ.get("JINA_API_KEY", None)

   
    LANGSMITH_TRACING: bool  = os.environ.get("LANGSMITH_TRACING", "false").lower() == "true"
    LANGSMITH_ENDPOINT: str  = os.environ.get("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    LANGSMITH_API_KEY: str   = os.environ.get("LANGSMITH_API_KEY", "")
    LANGSMITH_PROJECT: str   = os.environ.get("LANGSMITH_PROJECT", "finagent")

    
    LLM_MODEL: str = os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")

    @classmethod
    def validate(cls) -> bool:
        missing = [v for v in ["GROQ_API_KEY", "FINLIGHT_API_KEY"] if not getattr(cls, v)]
        if missing:
            print(f"❌ Missing required env vars: {', '.join(missing)}")
            return False
        return True

    @classmethod
    def setup_langsmith(cls) -> None:
        """
        Inject LangSmith env vars so LangChain picks them up automatically.
        Call this once at application startup before building the graph.
        """
        if cls.LANGSMITH_TRACING and cls.LANGSMITH_API_KEY:
            os.environ["LANGCHAIN_TRACING_V2"]  = "true"
            os.environ["LANGCHAIN_ENDPOINT"]     = cls.LANGSMITH_ENDPOINT
            os.environ["LANGCHAIN_API_KEY"]      = cls.LANGSMITH_API_KEY
            os.environ["LANGCHAIN_PROJECT"]      = cls.LANGSMITH_PROJECT
            print(
                f"✅ LangSmith tracing enabled  "
                f"(project: '{cls.LANGSMITH_PROJECT}', "
                f"endpoint: {cls.LANGSMITH_ENDPOINT})"
            )
        else:
            
            os.environ["LANGCHAIN_TRACING_V2"] = "false"


config = Config()

