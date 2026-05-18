from langchain_core.messages import HumanMessage, AIMessage
from agent.state import AgentState

state: AgentState = {
    "messages": [
        HumanMessage(content="How is Tesla doing?")
    ]
}

print(state)

state["messages"].append(
    AIMessage(content="Tesla looks bullish today.")
)

print("\nUpdated State:\n")
print(state)