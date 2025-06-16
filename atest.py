from ariadne import make_executable_schema
from ariadne import QueryType, gql, ObjectType
from ariadne.asgi import GraphQL
from pyjsg.jsglib import Object

query = QueryType()

@query.field("hello")
def resolve(x, info):
    print('x:', x)
    request = info.context["request"]
    user_agent = request.headers.get("user-agent", "guest")
    return "Hello, %s!" % user_agent


@query.field("include")
def resolve(x, info):
    print('x:', x)
    request = info.context["request"]
    user_agent = request.headers.get("user-agent", "guest")
    class Include:
        __identity__ = "Include-Class"

    return Include()

include = ObjectType("Include")

@include.field("inc")
def resolve(x, info):
    print('x:', x)
    request = info.context["request"]
    user_agent = request.headers.get("user-agent", "guest")
    return "Include, %s!" % user_agent



with open("xxx.graphql", "r") as f:
    schema = f.read()



schema = """
    type Include {
        inc: String!
    }
    type Query {
        hello: String!
        include: Include!
    }
"""

schema = gql(schema)

es = make_executable_schema(schema, query, include)

app = GraphQL(es, debug=True)
