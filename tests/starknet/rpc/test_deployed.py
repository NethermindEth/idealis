import pytest

from nethermind.idealis.rpc.starknet.core import get_current_block
from nethermind.idealis.rpc.starknet.deployed import get_erc20_info
from tests.addresses import STARKNET_ETH


@pytest.mark.asyncio
async def test_get_starknet_eth_erc20_info(async_http_session, starknet_rpc_url):
    erc20_info = await get_erc20_info(STARKNET_ETH, starknet_rpc_url, async_http_session)
    current_block = await get_current_block(async_http_session, starknet_rpc_url)

    assert erc20_info.name == "Ether"
    assert erc20_info.symbol == "ETH"
    assert erc20_info.decimals == 18
    assert erc20_info.total_supply >= 0
    assert erc20_info.update_block in (current_block, current_block - 1)
