from dataclasses import dataclass
from typing import Any

from nethermind.idealis.types.base import DataclassDBInterface

from .enums import TraceCallType, TraceError, TraceType


@dataclass(slots=True)
class Block:
    block_number: int
    block_hash: bytes
    timestamp: int

    parent_hash: bytes
    state_root: bytes
    miner: bytes
    extra_data: bytes
    nonce: bytes
    difficulty: int  # 0 if post-merge
    total_difficulty: int  # stays constant at 58750003716598352816469 post-merge
    size: int

    base_fee_per_gas: int  # manually set during block instantiation
    gas_limit: int
    gas_used: int


@dataclass(slots=True)
class Event:
    block_number: int
    transaction_index: int
    event_index: int

    contract_address: bytes
    data: bytes | None
    topics: list[bytes]

    event_name: str | None
    decoded_params: dict[str, Any] | None


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
    output: bytes | None


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
