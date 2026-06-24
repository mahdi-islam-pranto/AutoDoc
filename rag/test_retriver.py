from unittest import result

from doctor_search import langchain_documents, vectorstore
from searching.combined import hybrid_langchain_retriever

def test_hybrid_retriever():
    query = "I want to see a gynecology doctor for my pregnancy related symptoms. I have been experiencing nausea and fatigue. Can you recommend a doctor for me with their opeing hours?"
    result = hybrid_langchain_retriever(
        query=query,
        lc_documents=langchain_documents,
        vectorstore=vectorstore,
        k=6
    )

    print(f"retrieved documents: {result}")

# __init__ test
if __name__ == "__main__":
    test_hybrid_retriever()
