from dataclasses import dataclass
from typing import Any

from nethermind.idealis.types.base import DataclassDBInterface
from nethermind.idealis.types.starknet.enums import (
    BlockDataAvailabilityMode,
    EntryPointType,
    StarknetFeeUnit,
    StarknetTxType,
    TraceCallType,
    TransactionStatus,
)


@dataclass(slots=True)
class DecodedOperation:
    """
    Dataclass representing a decoded user operation.  If operation is unknown, the name will be set to
    'Unknown' and params set to the raw calldata inputs.
    """

    operation_name: str
    operation_params: dict[str, Any]


@dataclass(slots=True)
class Block(DataclassDBInterface):
    """
    Dataclass representing a block.
    """

    block_number: int
    timestamp: int

    block_hash: bytes
    parent_hash: bytes
    state_root: bytes
    sequencer_address: bytes
    l1_gas_price_wei: int
    l1_gas_price_fri: int
    l1_data_gas_price_wei: int | None
    l1_data_gas_price_fri: int | None
    l1_da_mode: BlockDataAvailabilityMode

    starknet_version: str
    transaction_count: int
    total_fee: int


@dataclass(slots=True)
class Transaction(DataclassDBInterface):
    transaction_hash: bytes
    block_number: int
    transaction_index: int

    type: StarknetTxType
    nonce: int
    signature: list[bytes]
    version: int
    timestamp: int
    status: TransactionStatus

    max_fee: int
    actual_fee: int
    fee_unit: StarknetFeeUnit
    execution_resources: dict[str, Any]
    gas_used: int | None

    # V3 Transaction Fields

    tip: int  # Not In Use
    resource_bounds: dict[str, int] | None  # Not in Use -- Will Eventually Enable Fee Market
    paymaster_data: list[bytes]
    account_deployment_data: list[bytes]  # Used in V3 transactions

    # data_availablity_mode: tuple[
    #     BlockDataAvailabilityMode | None,  # Fee Data Availability Mode
    #     BlockDataAvailabilityMode | None,  # Nonce Data Availability Mode
    # ]

    # Optional Fields for Different Tx Types
    contract_address: bytes | None
    selector: bytes  # Selector used for decoding calldata
    calldata: list[bytes]  # Calldata for Invoke Txns, Constructor Calldata for Depoly Account
    class_hash: bytes | None  # Deploy Account & Declare V2
    message_hash: bytes | None  # L1 Handler txns

    user_operations: list[DecodedOperation]
    revert_error: str | None


@dataclass(slots=True)
class TraceCall(DataclassDBInterface):
    """
    Condensed schema for trace data with just caller & recipient information & decoded data.
    Subset of Trace
    """

    block_number: int
    transaction_index: int
    trace_address: list[int]

    class_hash: bytes
    caller_address: bytes
    contract_address: bytes

    function_name: str
    decoded_inputs: dict[str, Any] | None
    decoded_outputs: dict[str, Any] | None


@dataclass(slots=True)
class Trace(DataclassDBInterface):
    block_number: int
    transaction_index: int
    trace_address: list[int]
    contract_address: bytes
    selector: bytes

    calldata: list[bytes]
    result: list[bytes]

    caller_address: bytes
    class_hash: bytes

    entry_point_type: EntryPointType | None
    call_type: TraceCallType | None
    execution_resources: dict[str, Any]

    error: str | None

    # Decoding Information
    function_name: str | None = None
    decoded_inputs: dict[str, Any] | None = None
    decoded_outputs: list[Any] | None = None


@dataclass(slots=True)
class Event(DataclassDBInterface):
    block_number: int
    transaction_index: int
    event_index: int

    contract_address: bytes
    class_hash: bytes | None

    keys: list[bytes]
    data: list[bytes]

    # Decoding Information
    event_name: str | None = None
    decoded_params: dict[str, Any] | None = None


@dataclass(slots=True)
class Message:
    block_number: int
    transaction_index: int
    message_index: int

    contract_address: str
    class_hash: str


@dataclass(slots=True)
class StateDiff:
    block_number: int
    tx_hash: bytes

    storage_diffs: list[dict[str, Any]]
    nonces: list[dict[str, Any]]
    deployed_contracts: list[Any]
    deprecated_declared_classes: list[Any]
    declared_classes: list[Any]
    replaced_classes: list[Any]
