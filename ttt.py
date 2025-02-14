
from dump_things_service.tests import model_0


inlined_json = """
{
  "id": "trr379:test_extract_1",
  "given_name": "Grandfather",
  "relations": {
    "trr379:test_extract_1_1": {
      "id": "trr379:test_extract_1_1",
      "given_name": "Father",
      "relations": {
        "trr379:test_extract_1_1_1": {
          "id": "trr379:test_extract_1_1_1",
          "acted_on_behalf_of": [
            "trr379:test_extract_1_1"
          ]
        }
      }
    },
    "trr379:test_extract_1_2": {
      "id": "trr379:test_extract_1_2",
      "at_time": "2028-12-31"
    }
  }
}
"""

a = model_0.Agent.model_validate_json('{"id": "trr379:agent_smith", "acted_on_behalf_of": ["trr379:agent_anne"]}')
print(a, flush=True)

x = model_0.Person.model_validate_json(inlined_json)
print(x, flush=True)
