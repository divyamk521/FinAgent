from langchain_core.messages import SystemMessage
from langchain_core.tracers.langchain import LangChainTracer
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_groq import ChatGroq

from agent.state import AgentState
from agent.tools import ALL_TOOLS
from config import config


SYSTEM_PROMPT = """You are FinAgent, a professional AI financial analyst.

You have access to the following tools:

- fetch_articles(query, language)   — Live market news and recent headlines.
- stock_price(symbol)               — Current price, day range, 52-week range, volume.
- stock_fundamentals(symbol)        — PE ratio, EPS, market cap, margins, and more.
- stock_technicals(symbol)          — Moving averages, RSI, trend signals.
- stock_forecast(symbol, market)    — Analyst consensus and price targets.

Guidelines:
- NSE (Indian) stocks: append '.NS' → e.g. 'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS'
- US stocks (NASDAQ/NYSE): plain ticker → e.g. 'AAPL', 'TSLA', 'GOOGL'
- Never guess financial data — always call the appropriate tool.
- Combine multiple tools when a thorough answer requires it.
- Present numbers clearly and explain what they mean for the investor.
"""

def _get_tracer() -> LangChainTracer | None:
    """Return a LangChainTracer when LangSmith tracing is enabled, else None."""
    if config.LANGSMITH_TRACING and config.LANGSMITH_API_KEY:
        return LangChainTracer(
            project_name=config.LANGSMITH_PROJECT,
        )
    return None

#binding llm with tools
def _get_llm_with_tools():
    llm = ChatGroq(
        model=config.LLM_MODEL,
        api_key=config.GROQ_API_KEY,
        temperature=0,
    )
    return llm.bind_tools(ALL_TOOLS)

#recieves Receives conversation history,tool results,previous responses

def ai_node(state: AgentState) -> dict:
    """Invoke the LLM, injecting the system prompt on the first turn."""
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    reply = _get_llm_with_tools().invoke(messages)
    return {"messages": [reply]}

def create_graph():
    """Build and compile the FinAgent StateGraph."""
    builder = StateGraph(AgentState)

    builder.add_node("ai", ai_node)
    builder.add_node("tools", ToolNode(ALL_TOOLS))

    builder.add_edge(START, "ai")
    builder.add_conditional_edges("ai", tools_condition)#if tools needed then tool calls or else end
    builder.add_edge("tools", "ai")

    tracer = _get_tracer()
    callbacks = [tracer] if tracer else []
    return builder.compile(checkpointer=None)


def invoke_graph(graph, messages: list, run_name: str = "finagent-run") -> dict:
    """
    Invoke the compiled graph with optional LangSmith tracing.

    Use this helper instead of graph.invoke() directly so every run
    is captured as a named trace in LangSmith.
    """
    tracer = _get_tracer()
    config_dict = {
        "run_name": run_name,
        "callbacks": [tracer] if tracer else [],
    }
    return graph.invoke({"messages": messages}, config=config_dict)