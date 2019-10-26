import logging
import json as _std_json
import importlib

json = _std_json

for __json_lib in ("orjson", "ujson", "rapidjson"):
    try:
        json = importlib.import_module(__json_lib)
        dumps = json.dumps
        loads = json.loads
        logging.info(f"{__name__}: Found {__json_lib} installed. Going to use it.")
        break
    except ImportError:
        continue
