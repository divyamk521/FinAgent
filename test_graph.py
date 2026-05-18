from langchain_core.messages import HumanMessage
from agent.graph import create_graph

graph = create_graph()

result = graph.invoke({
    "messages": [
        HumanMessage(content="What is the current price of Apple stock?")
    ]
})

print("\n=== FINAL STATE ===\n")
print(result)

print("\n=== MESSAGES ===\n")

for msg in result["messages"]:
    print(type(msg).__name__)
    print(msg)
    print("-" * 50)