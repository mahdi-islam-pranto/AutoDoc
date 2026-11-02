from langchain_openai import ChatOpenAI
# from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv()

chat_llm = ChatOpenAI(model="gpt-6", temperature=0)
# chat_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)