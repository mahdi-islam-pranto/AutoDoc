from graph.state import ConversationState
from utilities.prompts.prompts import prompts
from langchain_core.messages import SystemMessage
from service.invoke import invoke_service
from config.agent_setup import all_agents

# Supervisor prompt and valid agents
SUPERVISOR_INITIAL_PROMPT = prompts["supervisor"]["supervisor_initial_prompt"]

# Set of valid agents for safety check
VALID_AGENTS = all_agents

async def supervisor_node(state: ConversationState) -> dict:
    """
    The entry point for every user message.
    Reads current state + last message, picks the right agent.
    """

    # Only pass last 6 messages (3 turns) to save tokens
    recent_messages = state.messages[-6:] if len(state.messages) > 6 else state.messages
    # print(state.messages)
    
    stage = state.booking_stage.value if state.booking_stage else "none"

    #only print for checking the stage 
    # ── Build a state summary for the supervisor so it routes correctly ──
    state_context = (
        f"\n[SYSTEM STATE]\n"
        f"- booking_stage: {stage}\n"
        f"- selected_doctor_id: {state.selected_doctor_id or 'NOT SET'}\n"
        f"- selected_doctor_name: {state.selected_doctor_name or 'NOT SET'}\n"
        f"- patient_name: {state.patient_name or 'NOT SET'}\n"
        f"- patient_phone: {state.patient_phone or 'NOT SET'}\n"
        f"- symptoms: {state.symptoms or 'NOT SET'}\n"
    )  
    print(f"Supervisor Node - State Context: {state_context}")

    #uses the messages for invoke graph
    messages_with_context = [SystemMessage(content=state_context)] + list(recent_messages)
    
    #only print for checking the stage not core program context
    print(f"Supervisor Node - Current booking stage: {stage}, doctor_id: {state.selected_doctor_id}")

    # choose the agent by invoking the LLM with the supervisor prompt + recent conversation history
    response = await invoke_service(SUPERVISOR_INITIAL_PROMPT, messages_with_context)
    chosen_agent = response.content.strip().lower()
    
    # Debugging output to verify the LLM's response
    print(f"Supervisor chose agent: {chosen_agent}")  
    
    # Safety fallback — if LLM hallucinates an agent name
    if chosen_agent not in VALID_AGENTS:
        chosen_agent = "general_agent"
        
    # ── Hard guard: never route to booking without a confirmed doctor ID ──
    if chosen_agent == "booking_agent" and not state.selected_doctor_id:
        print("Supervisor: booking_agent requested but no doctor_id in state — redirecting to doctor_search_agent")
        chosen_agent = "doctor_search_agent"
        
    # update state with the chosen agent for the next node to read
    state.next_agent = chosen_agent

    return {"next_agent": chosen_agent}