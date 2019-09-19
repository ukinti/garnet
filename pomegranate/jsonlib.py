import json as _std_json
import importlib

__libs = {
    "orjson", "ujson",
}

json = _std_json

for __json_lib in __libs:
    try:
        json = importlib.import_module(__json_lib)
        dumps = json.dumps
        loads = json.loads
    except ImportError:
        continue
