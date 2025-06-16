
import strawberry


@strawberry.type
class Query:
    record: AllThings | None
    records: list[AllThings]

schema = strawberry.Schema(query=Query)
