from rag.load_doctor_document import load_doctor_documents
from rag.langchain_documents import convert_to_langchain_documents
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from rag.vector_store import create_faiss_vectorstore


# for new vectorstore creation and testing the retriever tools
# from load_doctor_document import load_doctor_documents
# from langchain_documents import convert_to_langchain_documents
# from langchain_community.vectorstores import FAISS
# from langchain_huggingface import HuggingFaceEmbeddings
# from vector_store import create_faiss_vectorstore

# todo: rag things here

# load the doctors document from the local system
documents = load_doctor_documents("documents/doctors.json")

# convert the raw documents to langchain documents
langchain_documents = convert_to_langchain_documents(documents)
# print("langchain_documents: ", langchain_documents)

# create the vectorstore
# vectorstore = create_faiss_vectorstore(langchain_documents)
# # check if the vectorstore is created successfully
# print("vectorstore created: ", vectorstore)

# load the vectorstore
vectorstore = FAISS.load_local(
        "vectorstore/db_faiss", 
        HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"),
        allow_dangerous_deserialization=True
        )


print("vectorstore loaded: ", vectorstore)


