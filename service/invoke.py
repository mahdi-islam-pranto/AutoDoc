from langchain_core.messages import SystemMessage, HumanMessage
from utilities.llms.llm import chat_llm 

# A helper function to invoke the LLM with a system prompt and recent messages.
async def invoke_service(system_prompt: str, recent_messages: list) -> SystemMessage:
    """
    A helper function to invoke the LLM with a system prompt and recent messages.
    This abstracts away the LLM invocation logic and can be reused across different nodes.
    """
    response = await chat_llm.ainvoke([
        SystemMessage(content=system_prompt),
        *recent_messages,
        HumanMessage(content="Based on the above conversation and system instructions, please provide your response.")
    ])
    return response

# This function is specifically for the general agent, which may have a different invocation pattern (e.g., using tools).
async def general_invoke(agent, state):

    result = await agent.ainvoke({"messages": state.messages})

    return {
            "messages": [result["messages"][-1]],
        }