from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from graph.state import ConversationState
from utilities.prompts.prompts import prompts
from service.invoke import general_invoke
from utilities.tools.general_info_tools import get_clinic_info
from utilities.llms.llm import chat_llm 

# Prompts
GENERAL_AGENT_INITIAL_PROMPT = prompts["general"]["general_agent_initial_prompt"]

async def general_agent_node(state: ConversationState) -> dict:
    agent = create_agent(
        model=chat_llm,
        tools=[get_clinic_info],
        system_prompt=GENERAL_AGENT_INITIAL_PROMPT
        
    )

    #korte hobe booking satge er kothae ache (handing)
    result = await general_invoke(agent, state)
    return result