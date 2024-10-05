import pytest

from nethermind.idealis.rpc.starknet.trace import trace_transaction
from nethermind.idealis.utils import to_bytes


@pytest.mark.asyncio
async def test_get_tx_trace(starknet_rpc_url, async_http_session):
    transaction_traces = await trace_transaction(
        transaction_hash=to_bytes("0x1eaebf1a9ff736c78d07b4948ad446ea179351d39b4ddcd9cc68a027fc23683"),
        rpc_url=starknet_rpc_url,
        aiohttp_session=async_http_session,
        block_number=480_000,
        transaction_index=1,
    )

    assert transaction_traces is not None
    assert transaction_traces.execute_traces[0].contract_address == to_bytes(
        "0x1fc0e4b571077b7bd1f5847412059a32cf7276dff16a94fad46988b1641f198", pad=32
    )
