from dataclasses import dataclass

from nethermind.idealis.types.base import DataclassDBInterface


class MessageSummary(DataclassDBInterface):
    message_hash: bytes
    status: str
    payload: list[bytes]
    timestamp: int

    starknet_transaction_hash: bytes
    starknet_block_number: int

    ethereum_transaction_hash: bytes
    ethereum_block_number: int

    from_address: bytes
    to_address: bytes

    direction: str
    selector: bytes
    nonce: int
    fee: int


@dataclass(slots=True)
class IncomingMessage(DataclassDBInterface):
    starknet_block_number: int
    starknet_transaction_index: int
    starknet_transaction_hash: bytes

    message_hash: bytes

    to_starknet_address: bytes
    calldata: list[bytes]
    selector: bytes


@dataclass(slots=True)
class OutgoingMessage(DataclassDBInterface):
    starknet_block_number: int
    starknet_transaction_index: int
    starknet_transaction_hash: bytes

    message_index: int  # Each message_sent can have multiple messages
    from_starknet_address: bytes
    to_ethereum_address: bytes
    payload: list[bytes]
