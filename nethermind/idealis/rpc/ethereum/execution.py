import logging
from typing import Any

import requests
from aiohttp import ClientSession

from nethermind.idealis.rpc.base.async_rpc import parse_async_rpc_response
from nethermind.idealis.rpc.ethereum.trace_parsing import (
    unpack_debug_trace_block_response,
    unpack_trace_block_response,
)

root_logger = logging.getLogger("nethermind")
logger = root_logger.getChild("rpc").getChild("ethereum").getChild("execution")


def current_block_req(url) -> dict[str, Any]:
    return {
        "url": url,
        "json": {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "eth_blockNumber",
        },
    }


async def get_current_block(rpc_url: str, session: ClientSession) -> int:
    logger.debug("Async Requesting Current Block Number")
    async with session.post(**current_block_req(rpc_url)) as response:
        response_json = await response.json()
        logger.debug(f"Async POST Returned -- Current Block Number: {response_json}")
        return int(response_json["result"], 16)


def sync_get_current_block(rpc_url: str) -> int:
    response = requests.post(**current_block_req(rpc_url))
    logger.debug(f"Sync POST Request -- Current Block Number: {response.json()}")
    return int(response.json()["result"], 16)


async def trace_block(
    block_number: int,
    rpc_url: str,
    aiohttp_session: ClientSession,
):
    logger.debug(f"Async POST -- trace_block {block_number}")

    async with aiohttp_session.post(
        url=rpc_url,
        json={
            "id": 1,
            "jsonrpc": "2.0",
            "method": "trace_block",
            "params": [block_number],
        },
    ) as response:
        block_traces = await parse_async_rpc_response(response)
        logger.debug(f"Async POST -- trace_block {block_number} returned {response.content_length} bytes")

        return unpack_trace_block_response(block_traces)


async def debug_trace_block(
    block_number: int,
    rpc_url: str,
    aiohttp_session: ClientSession,
):
    logger.debug(f"Requesting Nested Debug Traces for block {block_number}")

    async with aiohttp_session.post(
        url=rpc_url,
        json={
            "id": 1,
            "jsonrpc": "2.0",
            "method": "debug_traceBlockByNumber",
            "params": [block_number],
        },
    ) as response:
        block_traces = await parse_async_rpc_response(response)
        logger.debug(f"Finished Reading HTTP Response Bytes & Decoding JSON for Block {block_number} Debug Traces")

        return unpack_debug_trace_block_response(block_traces, block_number)
