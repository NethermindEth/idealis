import json
from pathlib import Path

RESOURCES_DIR = Path(__file__).parent / "resources"


def load_rpc_response(directory: str, file_name: str) -> dict:
    with open(RESOURCES_DIR / "rpc_responses" / directory / file_name, "r") as f:
        return json.load(f)
