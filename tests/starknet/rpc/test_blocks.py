import pytest

from nethermind.idealis.rpc.starknet import get_blocks_with_txns


@pytest.mark.asyncio
async def test_get_block(starknet_rpc_url, async_http_session):
    blocks, transactions, events, messages = await get_blocks_with_txns(
        blocks=[630_000], rpc_url=starknet_rpc_url, aiohttp_session=async_http_session
    )

    assert len(blocks) == 1
    assert len(transactions) == 127
    assert len(events) == 1025
    assert len(messages) == 0
