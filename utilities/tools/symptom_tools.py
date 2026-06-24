from langchain_core.tools import tool
from graph.state import ConversationState

# tool to search for symptom information and determine medical specialty
@tool
def search_symptom_info(symptoms: str) -> str:
    """Search for information about the user's symptoms to determine the appropriate medical specialty."""
    # In a real implementation, this would query a medical database or API.
    # Here we return a hardcoded response for demonstration.
    
    # update state
    # ConversationState.tool_call_made = "search_symptom_info"
    print(f"tool: search_symptom_info called with symptoms: {symptoms}")
    
    if "chest pain" in symptoms.lower():
        return "The user may need to see a cardiologist."
    elif "skin rash" in symptoms.lower():
        return "The user may need to see a dermatologist."
    elif "fever" in symptoms.lower() and "cough" in symptoms.lower():
        return "The user may need to see a pulmonologist."
    else:
        return "The user may need to see a general practitioner as no specific specialty is indicated in our symptom database."