
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dump_things_service.config import InstanceConfig


g_index = {}


def generate_index_for_collection(
    instance_config: InstanceConfig,
    collection_name: str,
) -> dict:

    index = {}

    global g_index
    g_index = {
        "name": "Dump Things Service",
        "description": "A service to dump various things.",
        "version": "1.0.0",
        "endpoints": [
            {
                "path": "/dump",
                "method": "POST",
                "description": "Dump the provided data."
            },
            {
                "path": "/status",
                "method": "GET",
                "description": "Get the status of the service."
            }
        ]
    }
    return g_index
