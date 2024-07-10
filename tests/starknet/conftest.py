import json

import pytest_asyncio

from nethermind.idealis.rpc.starknet import get_class_abis
from nethermind.starknet_abi.core import StarknetAbi
from nethermind.starknet_abi.dispatch import DecodingDispatcher


@pytest_asyncio.fixture(scope="function")
async def starknet_class_decoder(async_http_session, starknet_rpc_url):
    async def _generate_class_decoder(class_hashes: list[bytes]) -> DecodingDispatcher:
        dispatcher = DecodingDispatcher()

        class_abis = await get_class_abis(
            class_hashes=class_hashes,
            rpc_url=starknet_rpc_url,
            aiohttp_session=async_http_session,
        )

        for class_hash, abi in zip(class_hashes, class_abis, strict=True):
            if isinstance(abi, str):
                abi = json.loads(abi)

            parsed_abi = StarknetAbi.from_json(abi, abi_name="unknown", class_hash=class_hash)

            dispatcher.add_abi(parsed_abi)

        return dispatcher

    return _generate_class_decoder
