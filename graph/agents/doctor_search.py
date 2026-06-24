from langchain.agents import create_agent
from langchain_core.messages import ToolMessage
from graph.state import ConversationState, BookingStage
from utilities.llms.llm import chat_llm
from pydantic import BaseModel
from typing import List, Dict
import json
from utilities.tools.doctor_searching import doctor_search_rag_tool, doctor_confirmation_tool
from utilities.prompts.prompts import build_doctor_search_prompt
from service.tool_service import _extract_confirmed_doctor_from_messages


def doctor_search_agent_node(state: ConversationState) -> dict:
    # that uses the search_symptom_info tool to analyze the user's symptoms and determine the appropriate medical specialty.
    
    # get the last user message from state
    last_msg = state.messages[-1].content if state.messages else "No last message found"
    
    # get the latest symptoms from the state
    symptoms = ", ".join(state.symptoms) if state.symptoms else "none"
    
    # build a prompt for the LLM to recommend a doctor based on the symptoms and last user message
    llm_prompt = build_doctor_search_prompt(symptoms=symptoms, last_msg=last_msg)
    
    
    # make agent to recommend a doctor based on the llm_prompt
    agent = create_agent(
        model=chat_llm,
        system_prompt=llm_prompt,
        tools=[doctor_search_rag_tool, doctor_confirmation_tool],
        # response_format=DoctorSearchOutput
    )
    
    result = agent.invoke({"messages": state.messages})
    result_messages = result["messages"]
    last_agent_msg = result_messages[-1]

    # Extract confirmed doctor info directly from tool message history
    confirmed_doctor = _extract_confirmed_doctor_from_messages(result_messages)
    
    # update the state for booking stage
    # state.booking_stage = BookingStage.DOCTOR_SELECTION
    
    # update selected doctor info
    # state_update = {
    #     "messages": [last_agent_msg],
    #     "booking_stage": BookingStage.DOCTOR_SELECTION,
    #     "next_agent": "booking_agent",
    #     # Always write these keys — None if doctor not confirmed yet
    #     "selected_doctor_id": confirmed_doctor["doctor_id"] if confirmed_doctor else None,
    #     "selected_doctor_name": confirmed_doctor["doctor_name"] if confirmed_doctor else None,
    #     "selected_doctor_specialty": confirmed_doctor["specialty"] if confirmed_doctor else None,
    # }
    
    # ── Only advance stage and set doctor if confirmation tool actually fired ──
    if confirmed_doctor:
        print(f"Doctor Search Agent: Doctor confirmed — {confirmed_doctor}")
        return {
            "messages": [last_agent_msg],
            "booking_stage": BookingStage.DOCTOR_SELECTION,
            "next_agent": "booking_agent",
            "selected_doctor_id": confirmed_doctor["doctor_id"],
            "selected_doctor_name": confirmed_doctor["doctor_name"],
        }
    else:
        # Doctor not confirmed yet — stay in doctor search, don't touch doctor id
        print("Doctor Search Agent: No doctor confirmed yet, staying in doctor_search")
        return {
            "messages": [last_agent_msg],
            "booking_stage": BookingStage.SYMPTOM_COLLECTION,
            "next_agent": "doctor_search_agent",
            "selected_doctor_id": None,
            "selected_doctor_name": None,
        }
    
    # print(f"Doctor Search agent result: {state_update}")
    
    # return state_update