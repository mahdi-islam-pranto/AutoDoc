from langgraph.graph import StateGraph, START, END
from graph.state import ConversationState
from graph.supervisor.supervisor import supervisor_node
from graph.agents.symptom import symptom_agent_node
from graph.agents.general import general_agent_node
from graph.agents.doctor_search import doctor_search_agent_node
from graph.agents.booking import booking_agent_node

# Define the graph structure
def route_after_supervisor(state: ConversationState) -> str:
    """
    This edge function runs after supervisor_node.
    It reads state.next_agent (set by supervisor) and returns
    the name of the next node to run.
    """
    return state.next_agent

def build_graph(checkpointer):
    """Constructs the graph with nodes and edges."""
    
    graph = StateGraph(state_schema=ConversationState)
    
    # Add nodes
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("symptom_agent", symptom_agent_node)
    graph.add_node("doctor_search_agent", doctor_search_agent_node)
    graph.add_node("booking_agent", booking_agent_node)
    graph.add_node("general_agent", general_agent_node)
    
    # Add edges
    # --- Entry point ---
    # Every invocation starts at supervisor
    graph.set_entry_point("supervisor")
    
    # --- Conditional routing from supervisor ---
    # After supervisor runs, call route_after_supervisor()
    # which returns a string matching one of the edge targets below
    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "symptom_agent": "symptom_agent",
            "general_agent": "general_agent",
            "doctor_search_agent": "doctor_search_agent",
            "booking_agent": "booking_agent"
        }
    )
    
    # --- All agents go to END ---
    # After an agent responds, we're done for this turn.
    # State is saved. Next message re-enters at supervisor.
    for agent_name in ["symptom_agent", "general_agent", "doctor_search_agent", "booking_agent"]:
        graph.add_edge(agent_name, END)
            
        
    # Compile with the persistent checkpointer
    return graph.compile(checkpointer=checkpointer)