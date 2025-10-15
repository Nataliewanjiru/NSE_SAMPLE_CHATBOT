from content.chatbot_functions import ask_question 
from content.graphql_types import ChatResponse  

def ask_bot_resolver(question: str, user_id: str) -> ChatResponse:
    response = ask_question(question, user_id)
    return ChatResponse(reply=response)
