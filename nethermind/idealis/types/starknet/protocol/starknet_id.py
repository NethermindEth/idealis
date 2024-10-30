from dataclasses import dataclass
from typing import Any

from nethermind.idealis.types.base import DataclassDBInterface


@dataclass(slots=True)
class StarknetIDUpdate(DataclassDBInterface):
    domain_name: str

    block_number: int
    transaction_index: int
    event_index: int

    block_timestamp: int
    transaction_hash: bytes

    owner_update: bytes | None
    updated_user_data: bytes | None
    updated_verifier_data: bytes | None


class StarknetID(DataclassDBInterface):
    domain_name: bytes

    owner_address: bytes
    resolve_address: bytes
    expire_timestamp: int

    verifier_data: dict[str, Any]  # Discord, Twitter, Eth address, etc
    user_data: dict[str, Any]
