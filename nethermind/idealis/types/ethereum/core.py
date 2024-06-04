from dataclasses import dataclass
from typing import Optional

from nethermind.idealis.types.base import DataclassDBInterface

from .enums import TraceCallType, TraceError, TraceType


@dataclass(slots=True)
class BlockResponse:
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
class EventResponse:
    block_number: int
    transaction_index: int
    log_index: int

    contract_address: bytes
    data: Optional[bytes]
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
    error: Optional[TraceError]
    error_text: Optional[str]

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

    error: Optional[TraceError]
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

    error: Optional[TraceError]
    trace_type = TraceType.create
    from_address: bytes

    created_contract_address: bytes
    deployed_code: bytes


@dataclass(slots=True)
class Transaction:
    block_number: int
    transaction_hash: bytes
    transaction_index: int
    miner_address: bytes
    coinbase_transfer: int
    base_fee_per_gas: int
    gas_price: int
    gas_price_with_coinbase_transfer: int
    gas_used: int
    transaction_to_address: Optional[bytes]
    transaction_from_address: Optional[bytes]
