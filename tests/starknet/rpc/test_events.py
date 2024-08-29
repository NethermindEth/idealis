import pytest

from nethermind.idealis.rpc.starknet import get_events_for_contract
from nethermind.idealis.utils import to_bytes
from nethermind.starknet_abi.utils import starknet_keccak


@pytest.mark.asyncio
async def test_get_starknet_eth_transfers(starknet_rpc_url, async_http_session):
    events = await get_events_for_contract(
        contract_address=to_bytes("049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"),
        event_keys=[starknet_keccak(b"Transfer")],
        from_block=620_000,
        to_block=620_010,
        rpc_url=starknet_rpc_url,
        aiohttp_session=async_http_session,
    )

    for e in events:
        # There is no way to know tx & event index when querying events by contract
        assert e.transaction_index == -1  # Unknown
        assert e.event_index == -1  # Unknown

        assert e.contract_address == to_bytes("049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7")
        assert e.keys == [starknet_keccak(b"Transfer")]
