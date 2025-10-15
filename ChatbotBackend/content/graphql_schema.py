import strawberry
from content.graphql_resolvers import ask_bot_resolver
from content.graphql_types import ChatResponse 


@strawberry.type
class Query:
    @strawberry.field
    def ask_bot(self, question: str, user_id: str) -> ChatResponse:
        return ask_bot_resolver(question, user_id)


schema = strawberry.Schema(query=Query)