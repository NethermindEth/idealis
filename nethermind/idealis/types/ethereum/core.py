from dataclasses import dataclass
from typing import Any

from nethermind.idealis.types.base import DataclassDBInterface

from .enums import TraceCallType, TraceError, TraceType


@dataclass(slots=True)
class Block:
    block_number: int
    timestamp: int
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
class EventResponse:
    block_number: int
    transaction_index: int
    log_index: int

    contract_address: bytes
    data: bytes | None
    topics: list[bytes]


@dataclass(slots=True)
class RewardTraceResponse:
    block_number: int

    author: bytes
    reward_type: str
    value: int


@dataclass(slots=True)
class CallTraceResponse(DataclassDBInterface):
    block_number: int
    transaction_index: int
    trace_address: list[int]

    gas_supplied: int
    gas_used: int

    call_type: TraceCallType  # call, delegatecall, staticcall
    error: TraceError | None
    error_text: str | None

    value: int
    from_address: bytes
    to_address: bytes
    input: bytes
    output: bytes


@dataclass(slots=True)
class SuicideTraceResponse:
    block_number: int
    transaction_index: int
    trace_address: list[int]

    error: TraceError | None
    destroy_address: bytes
    refund_address: bytes
    balance: int


@dataclass(slots=True)
class CreateTraceResponse:
    block_number: int
    transaction_index: int
    trace_address: list[int]

    gas_supplied: int
    gas_used: int

    error: TraceError | None
    trace_type = TraceType.create
    from_address: bytes

    created_contract_address: bytes
    deployed_code: bytes


@dataclass(slots=True)
class Transaction:
    block_number: int
    transaction_hash: bytes
    transaction_index: int
    timestamp: int
    nonce: int
    type: int | None

    value: int
    gas_price: int | None
    gas_supplied: int
    gas_used: int | None
    max_priority_fee: int | None
    max_fee: int | None

    to_address: bytes | None
    from_address: bytes

    input: bytes | None
    decoded_input: dict[str, Any] | None
    function_name: str | None
