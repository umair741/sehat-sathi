from langgraph.graph import StateGraph, END
from app.agents.state import SehatSathiState
from app.agents.triage_agent import triage_node

graph = StateGraph(SehatSathiState)
graph.add_node("triage", triage_node)
graph.set_entry_point("triage")
graph.add_edge("triage", END)

compiled_graph = graph.compile()

if __name__ == "__main__":
    result = compiled_graph.invoke({
        "query": "yr bait karab h ",
        "severity": None,
        "reasoning": None,
        "health_response": None,
        "needs_booking": False,
        "booking_confirmation": None,
    })
    print(result)