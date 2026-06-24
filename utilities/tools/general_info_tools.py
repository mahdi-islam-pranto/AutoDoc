from langchain_core.tools import tool
from graph.state import ConversationState
from rag.doctor_search import langchain_documents, vectorstore
from rag.searching.combined import hybrid_langchain_retriever

# test clinic tool
CLINIC_INFO = {
    "hours": "Monday-Friday: 9am-6pm, Saturday: 10am-3pm, Sunday: Closed",
    "address": "123 Medical Center Road, Dhaka 1207",
    "phone": "+8802-555-0100",
    "emergency": "For emergencies, please call 999 or visit the nearest hospital.",
    "insurance": "We accept most major insurance plans. Call us to verify coverage.",
    "fees": "Consultation fee: 800-1500 BDT depending on specialist."
}


@tool
def get_clinic_info(topic: str) -> str:
    """
    Get general clinic information such as hours, address, fees, or insurance.
    Args:
        topic: One of: hours, address, phone, emergency, insurance, fees
    """
    topic_lower = topic.lower()
    for key, value in CLINIC_INFO.items():
        if key in topic_lower:
            return value
    # Return all info if topic doesn't match
    # update conversation state
    # ConversationState.tool_call_made = "get_clinic_info"
    print(f"tool: Clinic info tool called with topic: {topic}")
    return "\n".join(f"{k.title()}: {v}" for k, v in CLINIC_INFO.items())

