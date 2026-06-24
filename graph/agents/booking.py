from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from graph.state import ConversationState, BookingStage
from utilities.tools.booking_tools import get_available_slots, book_appointment
from utilities.llms.llm import chat_llm
from utilities.prompts.prompts import prompts
import datetime
import re

llm = chat_llm


def build_booking_prompt(state: ConversationState) -> str:
    """Builds a dynamic system prompt based on the current booking stage."""
    
    base = prompts["booking_agent_base_prompt"]

    context = f"""Current booking context:
- Stage: {state.booking_stage.value}
- Doctor: {state.selected_doctor_name or 'not selected'} (ID: {state.selected_doctor_id or 'N/A'})
- Slot: {state.selected_slot or 'not selected'}
- Patient name: {state.patient_name or 'not collected'}
- Patient phone: {state.patient_phone or 'not collected'}
- Symptoms: {', '.join(state.symptoms) if state.symptoms else 'none'}\n\n
- Today's date: {datetime.date.today().strftime('%B %d, %Y')}\n
\n"""

# instructions for each booking stage
    instructions = {
        BookingStage.DOCTOR_SELECTION: (
            "The user has been shown doctors. User might have selected a doctor or might be asking for more options. If doctor is not confirmed yet, confirm which doctor they want. If they ask for more options, show them again and confirm."
            "Confirm which doctor they want and ask what date they prefer."
            "If doctor is confirmed, move to the next stage and ask for preferred date for the appointment."
        ),
        BookingStage.SLOT_SELECTION: (
            "Call get_available_slots with the doctor_id and date. "
            "First check the user's message for a preferred time. If they mention one, confirm that it's available. If it's not available or they don't mention a time, ask them to choose from the available slots."
            "Present the available times clearly and ask which they prefer."
        ),
        BookingStage.CONFIRMING: (
            "You have a doctor and slot. "
            "If patient_name or patient_phone is missing, ask for them now. "
            "Once you have both, summarize the booking and ask for confirmation. "
            "When user confirms, call book_appointment."
            "Always confirm the details with the user before calling book_appointment."
        ),
        BookingStage.BOOKED: (
            "The booking is done. Thank the user and share the confirmation ID."
        ),
            
    }
    
    stage_instruction = instructions.get(state.booking_stage, "Guide the user through booking.")
    return base + context + "Your task: " + stage_instruction



async def booking_agent_node(state: ConversationState) -> dict:
    
    # if no doctor confirmed in state, send back to doctor search ──
    if not state.selected_doctor_id:
        print("Booking Agent: no selected_doctor_id in state — bouncing to doctor_search_agent")
        from langchain_core.messages import AIMessage
        return {
            "messages": [AIMessage(content="I need to find a doctor for you first. Let me help you with that.")],
            "next_agent": "doctor_search_agent",
        }
    
    prompt = build_booking_prompt(state)
    agent = create_agent(
        model=llm,
        tools=[book_appointment, get_available_slots],
        system_prompt=prompt
    )
    result = await agent.ainvoke({"messages": state.messages})
    last_msg = result["messages"][-1]

    updates: dict = {"messages": [last_msg]}

    # advance the booking stage by looking at tool calls made
    for msg in result["messages"]:
        # if book_appointment was called, we're done
        if hasattr(msg, "name") and msg.name == "book_appointment":
            conf_match = re.search(r"Confirmation ID: ([a-f0-9\-]{36})", msg.content)
            if conf_match:
                updates["booking_stage"] = BookingStage.BOOKED
                updates["confirmation_id"] = conf_match.group(1)

        # if get_available_slots was called, we moved to slot selection
        if hasattr(msg, "name") and msg.name == "get_available_slots":
            if state.booking_stage == BookingStage.DOCTOR_SELECTION:
                updates["booking_stage"] = BookingStage.SLOT_SELECTION

    # Extract patient info from the last AI message if mentioned
    content = last_msg.content
    phone_match = re.search(r"\+?\d[\d\s\-]{9,14}", content)
    if phone_match and not state.patient_phone:
        updates["patient_phone"] = phone_match.group(0)

    # if stage hasn't changed, advance it forward
    if "booking_stage" not in updates:
        stage_flow = {
            BookingStage.DOCTOR_SELECTION: BookingStage.SLOT_SELECTION,
            BookingStage.SLOT_SELECTION: BookingStage.CONFIRMING,
        }
        if state.booking_stage in stage_flow:
            updates["booking_stage"] = stage_flow[state.booking_stage]

    # return updated state 
    updated_state = {
        "messages": [last_msg],
        "booking_stage": updates.get("booking_stage", state.booking_stage),
        "patient_phone": updates.get("patient_phone", state.patient_phone),
    }

    return updated_state