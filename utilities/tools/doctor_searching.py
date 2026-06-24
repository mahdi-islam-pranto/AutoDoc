import json

from langchain_core.tools import tool
from graph.state import ConversationState
from rag.doctor_search import langchain_documents, vectorstore
from rag.searching.combined import hybrid_langchain_retriever


# doctor search tool for RAG
@tool
def doctor_search_rag_tool(query: str) -> str:
    """
    A tool that the doctor search agent can use to search for relevant doctor information based on the user's symptoms and query. This is a placeholder for the actual RAG retrieval function that will search the vectorstore and return relevant doctor information.
    Args:
        query: The query containing the user's symptoms/conditions/doctor name/department/specialization and needs, which will be used to retrieve relevant doctor information from the vectorstore.
    """
    
    # create retrival
    doctor_info = hybrid_langchain_retriever(
        query=query,
        lc_documents=langchain_documents,
        vectorstore=vectorstore,
        k=6
    )
    
    print(f"tool: Doctor search RAG tool called with query: {query}")
    print(f"tool: Retrieved doctor information: {doctor_info}")
    return f"Based on the query: {query}, we have retrieved the following doctor information: {doctor_info}"



@tool
def doctor_confirmation_tool(query: str) -> str:
    """
    A tool that the doctor search agent can use to confirm the user's choice of a doctor. This tool should be be called when the user selects a doctor or agrees to proceed with booking an appointment based on the doctor's recommendation. This tool will fetch the that selected doctor's information (id, name, degree, specialty, available slots, etc) from the vectorstore or database based on the user's previous queries and provided information, and confirm the user's choice before proceeding to the booking agent.
    Args:
        query: The query containing the user's selected doctor information. This will be used to confirm the user's choice and proceed with booking if they agree. the query can have the doctor's name, specialty, or agreement to proceed with booking based on the recommended doctor. 
    """
    
    # get doctor info
    doctor_info = hybrid_langchain_retriever(
        query=query,
        lc_documents=langchain_documents,
        vectorstore=vectorstore,
        k=1
    )

    print(f"tool: Doctor confirmation tool called with query: {query}")
    print(f"tool: Retrieved doctor information: {doctor_info}")

    documents = doctor_info.get("documents") if isinstance(doctor_info, dict) else []
    doctor_name = None
    doctor_id = None
    specialty = None
    opening_hours = None

# Extract doctor information from the retrieved documents, handling different possible formats
    if documents:
        first_doc = documents[0]
        # Depending on how the retriever formats the output, the doctor information might be in different places. We try to handle a few common cases here.
        if hasattr(first_doc, "metadata") and isinstance(first_doc.metadata, dict):
            doctor_name = first_doc.metadata.get("name")
            doctor_id = str(first_doc.metadata.get("id")) if first_doc.metadata.get("id") is not None else None
            specialty = first_doc.metadata.get("specialization")
            opening_hours = first_doc.metadata.get("opening_hours")
        elif isinstance(first_doc, dict):
            metadata = first_doc.get("metadata", {})
            doctor_name = metadata.get("name")
            doctor_id = str(metadata.get("id")) if metadata.get("id") is not None else None
            specialty = metadata.get("specialization")
            opening_hours = metadata.get("Opening_hours")
        elif isinstance(first_doc, str):
            import re
            name_match = re.search(r"Dr\.?\s*[^,\n]+", first_doc)
            id_match = re.search(r"(?:Doctor id|id)[:\s]*([0-9A-Za-z\-]+)", first_doc, re.IGNORECASE)
            spec_match = re.search(r"(?:specializing in|specialization[:]?)[\s]*([^\n,]+)", first_doc, re.IGNORECASE)
            opening_hours_match = re.search(r"(?:opening hours|available slots)[:\s]*([^\n]+)", first_doc, re.IGNORECASE)
            doctor_name = name_match.group(0).strip() if name_match else None
            doctor_id = id_match.group(1).strip() if id_match else None
            specialty = spec_match.group(1).strip() if spec_match else None
            opening_hours = opening_hours_match.group(1).strip() if opening_hours_match else None

    confirmed_doctor = {
        "doctor_name": doctor_name or "",
        "doctor_id": doctor_id or "",
        "specialty": specialty or "",
        "available_slots": opening_hours or ""
    }

    # Return as JSON string so ToolMessage.content is always parseable
    return json.dumps(confirmed_doctor)