import strawberry

@strawberry.type
class ChatResponse:
    reply: str