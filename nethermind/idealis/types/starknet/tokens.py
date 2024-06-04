from dataclasses import dataclass

from .core import DataclassDBInterface


@dataclass(slots=True)
class ERC20Transfer(DataclassDBInterface):
    block_number: int
    transaction_index: int
    event_index: int

    token_address: bytes
    from_address: bytes
    to_address: bytes
    value: int


@dataclass(slots=True)
class ERC721Transfer(DataclassDBInterface):
    block_number: int
    transaction_index: int
    event_index: int

    token_address: bytes
    from_address: bytes
    to_address: bytes
    token_id: bytes


@dataclass(slots=True)
class ERC1155Transfer:
    block_number: int
    transaction_index: int
    event_index: int

    token_address: bytes
    operator: bytes
    from_address: bytes
    to_address: bytes
    data_len: int
    token_ids: list[bytes]
    transfer_values: list[int]
