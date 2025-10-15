import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import BaseMessage
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain

# === Vectorstore Setup ===
embedding = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

vectorstore = Chroma(
    collection_name="gemini_pdf_chunks",
    embedding_function=embedding,
    persist_directory="./chroma_index"
)

retriever = vectorstore.as_retriever()

# === LLM Setup ===
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",  # or "gemini-1.5-pro"
    temperature=0.2,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# === Prompt Template ===
prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a helpful assistant for Nairobi Securities Exchange (NSE). "
        "Always refer to the context below when answering.\n\nContext:\n{context}"
    )),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

# === Memory Setup ===
user_memory_store = {}

from langchain_core.messages import HumanMessage, AIMessage
def ask_question(question: str, user_id: str) -> str:
    if user_id not in user_memory_store:
        user_memory_store[user_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    memory = user_memory_store[user_id]

    document_chain = create_stuff_documents_chain(llm, prompt)
    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    try:
        result = retrieval_chain.invoke({
            "input": question,
            "chat_history": memory.load_memory_variables({})["chat_history"]
        })

        response_text = result.get("answer", "No response.")

        # ✅ Update memory manually
        memory.chat_memory.add_message(HumanMessage(content=question))
        memory.chat_memory.add_message(AIMessage(content=response_text))

        return response_text
    except Exception as e:
        print(f"❌ Error in chain.invoke: {e}")
        return "An internal error occurred."
