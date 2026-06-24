def semantic_retriever(vectorstore, query, k=5):
    docs = vectorstore.similarity_search(query, k=k)
    results = [f"{doc.metadata['name']}, {doc.metadata['id']}, {doc.metadata['specialization']}\n {doc.page_content}" for doc in docs]

    return results
