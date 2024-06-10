from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EraBlock:

    block_number: int
    block_timestamp: int
    base_fee_per_gas: int  # manually set during block instantiation
    miner: bytes
    difficulty: int  # 0 if post-merge
    extra_data: bytes
    gas_limit: int
    gas_used: int
    hash: bytes
    nonce: bytes
    parent_hash: bytes
    size: int
    state_root: bytes
    total_difficulty: int  # stays constant at 58750003716598352816469 post-merge


@dataclass(slots=True)
class EraTransaction:

    transaction_hash: bytes
    block_number: int
    transaction_index: int
    timestamp: int
    gas_used: int
    error: str
    nonce: int
    from_address: bytes
    to_address: bytes
    input: bytes
    value: int
    gas_available: int
    gas_price: int
    decoded_signature: str | None
    decoded_input: dict[str, Any] | None
