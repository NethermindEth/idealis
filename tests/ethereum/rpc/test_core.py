import pytest

from nethermind.idealis.rpc.ethereum import get_blocks, get_events_for_contract
from nethermind.idealis.utils import to_bytes


@pytest.mark.asyncio
async def test_get_pre_london_block(eth_rpc_url, async_http_session):
    blocks, _ = await get_blocks([8_000_000], eth_rpc_url, async_http_session, full_transactions=False)

    assert len(blocks) == 1
    assert blocks[0].block_number == 8_000_000
    assert blocks[0].timestamp == 1561100149


@pytest.mark.asyncio
async def test_get_blocks(eth_rpc_url, async_http_session):
    blocks, transactions = await get_blocks([16_000_000], eth_rpc_url, async_http_session, full_transactions=False)

    assert len(blocks) == 1
    assert len(transactions) == 0

    assert blocks[0].block_number == 16_000_000
    assert blocks[0].timestamp == 1668811907
    assert blocks[0].base_fee_per_gas == 11130414489
    assert blocks[0].miner == to_bytes("ebec795c9c8bbd61ffc14a6662944748f299cacf")
    assert blocks[0].size == 76623


@pytest.mark.asyncio
async def test_get_blocks_with_txns(eth_rpc_url, async_http_session):
    blocks, transactions = await get_blocks([18_000_000], eth_rpc_url, async_http_session, full_transactions=True)

    assert len(blocks) == 1
    assert len(transactions) == 94

    assert transactions[9].to_address is None  # Contract creation
    assert len(transactions[9].input) == 14252


@pytest.mark.asyncio
async def test_get_weth_events(eth_rpc_url, async_http_session):
    events = await get_events_for_contract(
        contract_address=to_bytes("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"),
        rpc_url=eth_rpc_url,
        aiohttp_session=async_http_session,
        from_block=18_000_000,
        to_block=18_000_020,
        topics=[to_bytes("0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef")],
    )

    assert len(events) == 800
    assert events[0].block_number == 18_000_000
    assert events[0].transaction_index == 10
    assert events[-1].block_number == 18_000_019
    assert events[-1].transaction_index == 146
