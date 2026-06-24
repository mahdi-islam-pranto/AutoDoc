from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from graph.state import ConversationState, BookingStage
from utilities.tools.symptom_tools import search_symptom_info
from utilities.llms.llm import chat_llm 
from utilities.prompts.prompts import prompts

# get previous symptoms from state and include in prompt
# if ConversationState.symptoms:
#     previous_symptoms = ", ".join(ConversationState.symptoms)
# else:
#     previous_symptoms = "none"
# current_booking_stage = ConversationState.booking_stage.value if ConversationState.booking_stage else "none"

symptom_agent_initial_prompt = prompts["symptom"]["symptom_agent_initial_prompt"]

# This function builds a dynamic system prompt for the symptom agent based on the user's current symptoms and booking stage. It provides context to the LLM to make more informed recommendations.
def build_symptom_prompt(state: ConversationState) -> str:
    """Builds a dynamic system prompt based on the user's symptoms and booking stage."""
    base = """You are a compassionate medical triage assistant for our iHelpBD healthcare platform. Your goal is to help users understand their symptoms and guide them to the right type of doctor of ours. You will always end reply with like, "Would you like to see a doctor of ours based on your symptoms?" """
    symptom_info = f"User's current or reported symptoms: {', '.join(state.symptoms) if state.symptoms else 'none'}.\n\n"
    instructions = (
        symptom_agent_initial_prompt
    )

    return f"{base}\n\n{symptom_info}{instructions}"


# main agent node function that will be called by the graph when routing to symptom_agent
async def symptom_agent_node(state: ConversationState) -> dict:
    agent = create_agent(
        model=chat_llm,
        tools=[search_symptom_info],
        system_prompt=build_symptom_prompt(state)
    )
    
    result = await agent.ainvoke({"messages": state.messages})
    last_msg = result["messages"][-1]

    # Collect symptoms from recent user messages
    recent_symptoms = [
        m.content for m in state.messages[-2:]
        if hasattr(m, "type") and m.type == "human"
    ]
    
    # update symptom state with recent symptoms mentioned by the user
    updated_symptoms = [*state.symptoms, *recent_symptoms]
    
    # update BookingStage to SYMPTOM_COLLECTION after collecting symptoms
    state.booking_stage = BookingStage.SYMPTOM_COLLECTION
    
    print(f"Updated symptoms in state: {updated_symptoms}")
    print(f"Updated booking stage in state: {state.booking_stage.value}")
    
    return {
        "messages": [last_msg],
        "symptoms": updated_symptoms,
        "booking_stage": BookingStage.SYMPTOM_COLLECTION,
        "next_agent": "doctor_search_agent"
    }