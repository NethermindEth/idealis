import pytest

from nethermind.idealis.rpc.ethereum import get_blocks
from nethermind.idealis.utils import to_bytes


@pytest.mark.asyncio
async def test_get_blocks(eth_rpc_url, async_http_session):
    blocks, transactions = await get_blocks([16_000_000], eth_rpc_url, async_http_session, full_transactions=False)

    assert len(blocks) == 1
    assert len(transactions) == 0

    assert blocks[0].block_number == 16_000_000
    assert blocks[0].block_timestamp == 1668811907
    assert blocks[0].base_fee_per_gas == 11130414489
    assert blocks[0].miner == to_bytes("ebec795c9c8bbd61ffc14a6662944748f299cacf")
    assert blocks[0].size == 76623
