import asyncio

from aiohttp import ClientSession

from nethermind.idealis.rpc.starknet import get_current_block, starknet_call
from nethermind.idealis.types.base.tokens import ERC20TokenData
from nethermind.idealis.utils import to_bytes
from nethermind.starknet_abi.utils import starknet_keccak


async def get_erc20_info(
    contract: bytes,
    json_rpc: str,
    client_session: ClientSession,
) -> ERC20TokenData | None:
    block_number, name, symbol, decimals, total_supply_camel, total_supply_snake = await asyncio.gather(
        get_current_block(client_session, json_rpc),
        starknet_call(contract, starknet_keccak(b"name"), [], client_session, json_rpc),
        starknet_call(contract, starknet_keccak(b"symbol"), [], client_session, json_rpc),
        starknet_call(contract, starknet_keccak(b"decimals"), [], client_session, json_rpc),
        starknet_call(contract, starknet_keccak(b"totalSupply"), [], client_session, json_rpc),
        starknet_call(contract, starknet_keccak(b"total_supply"), [], client_session, json_rpc),
    )

    if name is None and symbol is None and decimals is None:
        return None

    if total_supply_camel:
        total_supply = int(total_supply_camel[0], 16)
    elif total_supply_snake:
        total_supply = int(total_supply_snake[0], 16)
    else:
        total_supply = None

    return ERC20TokenData(
        address=contract,
        name=to_bytes(name[0]).decode("utf-8") if name else None,
        symbol=to_bytes(symbol[0]).decode("utf-8") if symbol else None,
        decimals=int(decimals[0], 16) if decimals else None,
        total_supply=total_supply,
        update_block=block_number,
    )
