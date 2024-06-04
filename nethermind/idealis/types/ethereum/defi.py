# from dataclasses import dataclass
#
#
# @dataclass(slots=True)
# class AssetBorrow:
#     block_number: int
#     transaction_hash: bytes
#     trace_address: list[int]
#     protocol: Protocol
#     token_address: bytes
#     user_address: bytes
#     on_behalf_of_address: bytes
#     borrow_amount: int
#
#
# @dataclass(slots=True)
# class AssetSupply:
#     block_number: int
#     transaction_hash: bytes
#     trace_address: list[int]
#     protocol: Protocol
#     token_address: bytes
#     user_address: bytes
#     on_behalf_of_address: bytes
#     supply_amount: int
#
#
# @dataclass(slots=True)
# class Swap:
#     abi_name: str
#     transaction_hash: bytes
#     transaction_index: int
#     block_number: int
#     trace_address: list[int]
#     contract_address: bytes
#     from_address: bytes
#     to_address: bytes
#     token_in_address: bytes
#     token_in_amount: int
#     token_out_address: bytes
#     token_out_amount: int
#     protocol: Protocol
#     error: TraceError | None
#
#
# @dataclass(slots=True)
# class Liquidation:
#     liquidated_user: bytes
#     liquidator_user: bytes
#     debt_token_address: bytes
#     debt_purchase_amount: int
#     received_amount: int
#     received_token_address: bytes | None
#     protocol: Protocol
#     transaction_hash: bytes
#     trace_address: list[int]
#     block_number: str
#     error: TraceError | None
#
#
# @dataclass(slots=True)
# class NftTrade:
#     abi_name: str
#     transaction_hash: bytes
#     transaction_index: int
#     block_number: int
#     trace_address: list[int]
#     protocol: Protocol | None
#     error: TraceError | None
#     seller_address: bytes
#     buyer_address: bytes
#     payment_token_address: bytes
#     payment_amount: int
#     collection_address: bytes
#     token_id: int
#
#
# @dataclass(slots=True)
# class Transfer:
#     block_number: int
#     transaction_hash: bytes
#     trace_address: list[int]
#     from_address: bytes
#     to_address: bytes
#     amount: int
#     token_address: bytes
