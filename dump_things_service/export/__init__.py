
from pathlib import Path

from .json import export_json
from .tree import export_tree


exporter_info = {
    'to': (export_json, Path),
    'json': (export_json, Path),
    'tree': (export_tree, Path),
}
