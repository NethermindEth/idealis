from dataclasses import dataclass

from .db_interface import DataclassDBInterface


@dataclass(slots=True)
class ERC20TokenData(DataclassDBInterface):
    address: bytes
    name: str | None
    symbol: str | None
    decimals: int | None
    total_supply: int | None
    update_block: int


@dataclass(slots=True)
class ERC721TokenData(DataclassDBInterface):
    name: str | None
    symbol: str | None
    total_supply: int | None
    update_block: int


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
class ERC20BalanceDiff(DataclassDBInterface):
    token_address: bytes
    holder_address: bytes
    block_number: int

    total_supply_diff: int  # Amount diff in total_supply
    balance_diff: int
    transfers_received: int
    transfers_sent: int
