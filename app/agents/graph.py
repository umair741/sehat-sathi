from langgraph.graph import StateGraph, END
from app.agents.state import SehatSathiState
from app.agents.supervisor import supervisor_node
from app.agents.triage_agent import triage_node
from app.agents.health_info_agent import health_info_node


def booking_node(state: SehatSathiState) -> SehatSathiState:
    state["booking_confirmation"] = {"status": "pending", "message": "Booking agent coming soon."}
    return state


def general_node(state: SehatSathiState) -> SehatSathiState:
    state["health_response"] = "Assalam o Alaikum! Main Sehat Sathi hoon. Apni sehat ke baare mein kuch bhi pooch sakte hain."
    return state


# --- Routing function ---

def route_supervisor(state: SehatSathiState) -> str:
    return state.get("route_to", "general")


# --- Build graph ---

graph = StateGraph(SehatSathiState)

# Add nodes
graph.add_node("supervisor", supervisor_node)
graph.add_node("triage", triage_node)
graph.add_node("health_info", health_info_node)
graph.add_node("booking", booking_node)
graph.add_node("general", general_node)

# Entry point
graph.set_entry_point("supervisor")

# Conditional edges from supervisor
graph.add_conditional_edges(
    "supervisor",
    route_supervisor,
    {
        "triage": "triage",
        "health_info": "health_info",
        "booking": "booking",
        "general": "general",
    },
)

# All agents go to END
graph.add_edge("triage", END)
graph.add_edge("health_info", END)
graph.add_edge("booking", END)
graph.add_edge("general", END)

compiled_graph = graph.compile()


if __name__ == "__main__":
    # --- Print graph structure ---
    print("=== Graph Structure (ASCII) ===")
    compiled_graph.get_graph().print_ascii()

    print("\n=== Graph Structure (Mermaid) ===")
    print(compiled_graph.get_graph().draw_mermaid())

    print("\n=== Running Test Queries ===")
    test_queries = [
        "seene me dard hai",
        "diabetes kya hai?",
        "appointment chahiye",
        "hello",
    ]
    for query in test_queries:
        result = compiled_graph.invoke({
            "query": query,
            "route_to": None,
            "severity": None,
            "reasoning": None,
            "health_response": None,
            "needs_booking": False,
            "booking_confirmation": None,
        })
        print(f"\nQuery: {query}")
        print(f"  Route: {result.get('route_to')}")
        if result.get('severity'):
            print(f"  Severity: {result.get('severity')}")
        if result.get('reasoning'):
            print(f"  Reasoning: {result.get('reasoning')}")
        if result.get('health_response'):
            print(f"  Health response: {result.get('health_response')}")
        if result.get('booking_confirmation'):
            print(f"  Booking: {result.get('booking_confirmation')}")