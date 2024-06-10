import asyncio
import logging

from aiohttp import ClientSession

from nethermind.idealis.parse.starknet.trace import (
    ParsedBlockTrace,
    unpack_trace_block_response,
)
from nethermind.idealis.rpc.base.async_rpc import parse_eth_rpc_async_response

root_logger = logging.getLogger("nethermind")
logger = root_logger.getChild("rpc").getChild("starknet").getChild("trace")


async def trace_blocks(
    block_numbers: list[int],
    rpc_url: str,
    aiohttp_session: ClientSession,
) -> ParsedBlockTrace:
    logger.info(f"Requesting Traces for {len(block_numbers)} Blocks")

    async def _trace_block(block_number: int):
        async with aiohttp_session.post(
            url=rpc_url,
            json={
                "id": 1,
                "jsonrpc": "2.0",
                "method": "starknet_traceBlockTransactions",
                "params": {"block_id": {"block_number": block_number}},
            },
        ) as response:
            block_traces = await parse_eth_rpc_async_response(response)
            logger.debug(f"trace_blocks -> {block_number} returned {response.content.total_bytes} json bytes")
            try:
                return unpack_trace_block_response(block_traces, block_number)
            except BaseException as e:
                logger.error(f"Error parsing block traces {block_number}: {e}")
                raise e

    block_traces: tuple[ParsedBlockTrace] = await asyncio.gather(
        *[_trace_block(block_number) for block_number in block_numbers]
    )

    return ParsedBlockTrace.from_block_traces([*block_traces])
