import asyncio
import logging
from typing import Any, Sequence

import requests
from aiohttp import ClientSession

from nethermind.idealis.parse.ethereum.execution import (
    parse_get_block_response,
    parse_get_logs_response,
)
from nethermind.idealis.parse.ethereum.trace import (
    unpack_debug_trace_block_response,
    unpack_trace_block_response,
)
from nethermind.idealis.rpc.base.async_rpc import parse_async_rpc_response
from nethermind.idealis.types.ethereum import Block, Event, Transaction
from nethermind.idealis.utils import to_hex

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


async def get_blocks(
    blocks: list[int], rpc_url: str, aiohttp_session: ClientSession, full_transactions: bool = True
) -> tuple[Sequence[Block], Sequence[Transaction]]:
    logger.debug(f"Async POST -- get {len(blocks)} blocks")

    async def _get_block(num: int) -> tuple[Block, list[Transaction]]:
        async with aiohttp_session.post(
            url=rpc_url,
            json=(
                payload := {
                    "id": 1,
                    "jsonrpc": "2.0",
                    "method": "eth_getBlockByNumber",
                    "params": [hex(num), full_transactions],
                }
            ),
        ) as response:
            block_json = await parse_async_rpc_response(payload, response)
            logger.debug(f"Async POST -- get {len(blocks)} blocks returned {response.content_length} bytes")

            return parse_get_block_response(block_json)

    block_data = await asyncio.gather(*[_get_block(block) for block in blocks])
    output_blocks, output_transactions = [], []
    for block, transactions in block_data:
        output_blocks.append(block)
        output_transactions.extend(transactions)
    return output_blocks, output_transactions


async def trace_block(
    block_number: int,
    rpc_url: str,
    aiohttp_session: ClientSession,
):
    logger.debug(f"Async POST -- trace_block {block_number}")

    async with aiohttp_session.post(
        url=rpc_url,
        json=(
            payload := {
                "id": 1,
                "jsonrpc": "2.0",
                "method": "trace_block",
                "params": [block_number],
            }
        ),
    ) as response:
        block_traces = await parse_async_rpc_response(payload, response)
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
        json=(
            payload := {
                "id": 1,
                "jsonrpc": "2.0",
                "method": "debug_traceBlockByNumber",
                "params": [block_number],
            }
        ),
    ) as response:
        block_traces = await parse_async_rpc_response(payload, response)
        logger.debug(f"Finished Reading HTTP Response Bytes & Decoding JSON for Block {block_number} Debug Traces")

        return unpack_debug_trace_block_response(block_traces, block_number)


async def get_events_for_contract(
    contract_address: bytes | list[bytes],
    topics: list[bytes | list[bytes]],
    from_block: int,
    to_block: int,
    rpc_url: str,
    aiohttp_session: ClientSession,
) -> list[Event]:
    """
    Get all events for a contract address within a block range.

    :param contract_address:
        Contract address to get events for.  Can also pass a list of contract addresses
    :param topics:
        List of topics to filter events by.  The first topic is the event signature, and the rest are indexed parameters.
    :param from_block: Inclusive From block.  Can be "earliest" or an integer number
    :param to_block: Can be "latest" or an integer number.  If an int to_block is specified, it is exclusive.
    :param rpc_url: JSON RPC URL implementing the eth_getLogs method
    :param aiohttp_session:
    """
    async with aiohttp_session.post(
        rpc_url,
        json=(
            payload := {
                "jsonrpc": "2.0",
                "method": "eth_getLogs",
                "params": [
                    {
                        "address": to_hex(contract_address, pad=20)
                        if isinstance(contract_address, bytes)
                        else [to_hex(addr, pad=20) for addr in contract_address],
                        "fromBlock": hex(from_block) if isinstance(from_block, int) else from_block,
                        "toBlock": hex(to_block - 1) if isinstance(to_block, int) else to_block,
                        "topics": [
                            to_hex(topic) if isinstance(topic, bytes) else [to_hex(t) for t in topic]
                            for topic in topics
                        ],
                    }
                ],
                "id": 1,
            }
        ),
    ) as events_response:
        events_json = await parse_async_rpc_response(payload, events_response)

        return parse_get_logs_response(events_json)
