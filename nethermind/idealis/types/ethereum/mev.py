# from dataclasses import dataclass
#
# from .defi import Swap
#
#
# @dataclass(slots=True)
# class Arbitrage:
#     swaps: list[Swap]
#     block_number: int
#     transaction_hash: bytes
#     account_address: bytes
#     profit_token_address: bytes
#     start_amount: int
#     end_amount: int
#     profit_amount: int
#     error: TraceError | None
#
#
# @dataclass(slots=True)
# class Sandwich:
#     block_number: int
#     sandwicher_address: bytes
#     frontrun_swap: Swap
#     backrun_swap: Swap
#     sandwiched_swaps: list[Swap]
#     profit_token_address: bytes
#     profit_amount: int
#
#
# @dataclass(slots=True)
# class JITLiquidity:
#     block_number: int
#     bot_address: bytes | None
#     pool_address: bytes
#     mint_transaction_hash: bytes
#     mint_transaction_trace: list[int]
#     burn_transaction_hash: bytes
#     burn_transaction_trace: list[int]
#     swaps: list[Swap]
#     token0_address: bytes
#     token1_address: bytes
#     mint_token0_amount: int
#     mint_token1_amount: int
#     burn_token0_amount: int
#     burn_token1_amount: int
#     token0_swap_volume: int
#     token1_swap_volume: int
