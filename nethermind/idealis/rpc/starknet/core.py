import asyncio
import json
import logging
from typing import Any, Sequence

import requests
from aiohttp import ClientSession

from nethermind.idealis.exceptions import RPCError
from nethermind.idealis.parse.starknet.block import (
    parse_block,
    parse_block_with_tx_receipts,
)
from nethermind.idealis.parse.starknet.event import parse_event_response
from nethermind.idealis.rpc.base.async_rpc import parse_async_rpc_response
from nethermind.idealis.types.starknet.core import Block, Event, Transaction
from nethermind.idealis.types.starknet.rollup import OutgoingMessage
from nethermind.idealis.utils import to_bytes, to_hex

root_logger = logging.getLogger("nethermind")
logger = root_logger.getChild("rpc").getChild("starknet")


def _starknet_block_id(block_id: int | str | bytes) -> str | dict[str, str | int]:
    """
    Parses Starknet block id into proper form.  if block_id is string like 'latest', returns that string.
    If bytes are passed, returns '{"block_hash": "0x..."}'.  If int is passed, returns as block number
    '{"block_number": ...}'

    :param block_id:
    :return:
    """
    if isinstance(block_id, str):
        return block_id
    elif isinstance(block_id, bytes):
        return {"block_hash": to_hex(block_id)}
    elif isinstance(block_id, int):
        return {"block_number": block_id}
    else:
        raise ValueError(f"Cannot parse {block_id} into starknet block_id")


async def get_current_block(aiohttp_session: ClientSession, json_rpc: str) -> int:
    async with aiohttp_session.post(
        json_rpc,
        json=(
            payload := {
                "jsonrpc": "2.0",
                "method": "starknet_blockNumber",
                "params": {},
                "id": 1,
            }
        ),
    ) as latest_block_resp:
        response_json = await parse_async_rpc_response(payload, latest_block_resp)

        return int(response_json)


def sync_get_current_block(rpc_url) -> int:
    """Get the current block number."""

    block_response = requests.post(
        rpc_url,
        json={
            "jsonrpc": "2.0",
            "method": "starknet_blockNumber",
            "params": {},
            "id": 1,
        },
        timeout=20,
    )
    response_json = block_response.json()
    try:
        return int(response_json["result"])
    except KeyError:  # pylint: disable=raise-missing-from
        raise RPCError(f"Error fetching current block number for Starknet: {response_json}")


async def get_blocks(blocks: list[int], rpc_url: str, aiohttp_session: ClientSession) -> Sequence[Block]:
    logger.debug(f"Async Requesting {len(blocks)} Blocks")

    async def _get_block(block_number: int) -> Block:
        async with aiohttp_session.post(
            rpc_url,
            json=(
                payload := {
                    "jsonrpc": "2.0",
                    "method": "starknet_getBlockWithTxHashes",
                    "params": {"block_id": _starknet_block_id(block_number)},
                    "id": 1,
                }
            ),
        ) as block_response:
            block_json = await parse_async_rpc_response(payload, block_response)
            return parse_block(block_json)

    response_data = await asyncio.gather(*[_get_block(block) for block in blocks])
    return response_data


async def get_blocks_with_txns(
    blocks: list[int], rpc_url: str, aiohttp_session: ClientSession
) -> tuple[list[Block], list[Transaction], list[Event], list[OutgoingMessage]]:
    logger.debug(f"Async Requesting {len(blocks)} Blocks with Transactions")

    async def _get_block(
        block_number: int,
    ) -> tuple[Block, list[Transaction], list[Event], list[OutgoingMessage]]:
        async with aiohttp_session.post(
            rpc_url,
            json=(
                payload := {
                    "jsonrpc": "2.0",
                    "method": "starknet_getBlockWithReceipts",
                    "params": {"block_id": _starknet_block_id(block_number)},
                    "id": 1,
                }
            ),
        ) as response:
            block_json = await parse_async_rpc_response(payload, response)
            logger.debug(f"get_blocks_with_txns -> {block_number} returned {response.content.total_bytes} json bytes")
            try:
                return parse_block_with_tx_receipts(block_json)
            except BaseException as e:
                logger.error(f"Error parsing block {block_number}: {e}")
                raise e

    response_data: tuple[tuple[Block, list[Transaction], list[Event], list[OutgoingMessage]]] = await asyncio.gather(
        *[_get_block(block) for block in blocks]
    )

    out_blocks, out_txns, out_events, out_messages = [], [], [], []
    for block, txns, events, messages in response_data:
        out_blocks.append(block)
        out_txns += txns
        out_events += events
        out_messages += messages

    return out_blocks, out_txns, out_events, out_messages


def sync_get_class_abi(
    class_hash: bytes,
    rpc_url: str,
    block_number: int | None = None,
    timeout: int = 40,
) -> list[dict[str, Any]] | None:
    """
    Synchronously get the ABI of a Starknet class.
    """
    logger.debug(f"Sync Requesting Starknet Class ABI for {to_hex(class_hash)}")

    class_response = requests.post(
        rpc_url,
        json={
            "jsonrpc": "2.0",
            "method": "starknet_getClass",
            "params": {"class_hash": to_hex(class_hash), "block_id": _starknet_block_id(block_number or "latest")},
            "id": 1,
        },
        timeout=timeout,
    )

    class_json = class_response.json()

    if "error" in class_json:
        return None

    try:
        rpc_abi_response = class_json["result"]["abi"]
    except KeyError:  # pylint: disable=raise-missing-from
        raise RPCError(f"Error fetching Starknet class ABI for {to_hex(class_hash)}: {class_json}")

    if isinstance(rpc_abi_response, str):
        try:
            class_abi = json.loads(rpc_abi_response)
        except json.JSONDecodeError:
            logger.error(f"Invalid ABI for class 0x{class_hash.hex()}.  Could not parse ABI JSON...")
            return None
    else:
        # ABI Is already decoded into dict with response.json()
        class_abi = rpc_abi_response

    if class_abi is None or len(class_abi) == 0:
        logger.warning(f"Empty ABI for class 0x{class_hash.hex()}")
        return None

    return class_abi


async def get_class_abis(
    class_hashes: list[bytes], rpc_url: str, aiohttp_session: ClientSession
) -> Sequence[list[dict[str, Any]] | None]:
    logger.debug(f"Async Requesting {len(class_hashes)} Starknet Class Abis")

    async def _get_class(class_hash: bytes):
        async with aiohttp_session.post(
            rpc_url,
            json={
                "jsonrpc": "2.0",
                "method": "starknet_getClass",
                "params": {"class_hash": to_hex(class_hash), "block_id": "latest"},
                "id": 1,
            },
        ) as class_response:
            # Handle this manually since an 'error' should be returned as None instead of raising Exception
            response_json = await class_response.json()  # Async read response bytes
            class_response.release()  # Release the connection back to the pool, keeping TCP conn alive

            if "error" in response_json:
                return None

            return response_json["result"]["abi"]

    class_abis = await asyncio.gather(*[_get_class(class_hash) for class_hash in class_hashes])
    return class_abis


async def get_contract_impl_class(
    contract_address: bytes,
    block_id: str | int | bytes,
    rpc_url: str,
    aiohttp_session: ClientSession,
) -> bytes:
    """
    Get the class hash of the contract implementation at the given block.

    :param contract_address:
    :param block_id:
    :param rpc_url:
    :param aiohttp_session:
    :return:
    """
    async with aiohttp_session.post(
        rpc_url,
        json=(
            payload := {
                "jsonrpc": "2.0",
                "method": "starknet_getClassHashAt",
                "params": {
                    "block_id": _starknet_block_id(block_id),
                    "contract_address": to_hex(contract_address),
                },
                "id": 1,
            }
        ),
    ) as response:
        contract_json = await parse_async_rpc_response(payload, response)
        return to_bytes(contract_json["class_hash"], pad=32)


async def get_events_for_contract(
    contract_address: bytes,
    event_keys: list[bytes],
    from_block: int,
    to_block: int,
    rpc_url: str,
    aiohttp_session: ClientSession,
    page_size: int = 1024,
) -> list[Event]:
    """
    Get all starknet events in a block range

    .. warning:
        THIS METHOD CAN BE SUPER EXPENSIVE...  If an RPC node sets a low MAX-SCAB-BLOCKS-GET-EVENTS in the config,
        this will result in hundreds or thousands of paginated calls...

    :param contract_address: Contract to search
    :param event_keys: list of event selectors to query
    :param from_block: inclusive from block
    :param to_block: exclusive to block
    :param rpc_url:
    :param aiohttp_session:
    :param page_size: Number of events to return per query.  Defaults to max page size
    :return: [Event]
    """

    async def _get_page_of_events(_continuation_token: str | None = None) -> tuple[list[Event], str | None]:
        request_params = {
            "filter": {
                "from_block": _starknet_block_id(from_block),
                "to_block": _starknet_block_id(to_block - 1),
                "address": to_hex(contract_address, pad=32),
                "keys": [
                    [to_hex(key, pad=32) for key in event_keys]  # Key[0] searches event_selector...
                    # Additional keys can search through indexed event keys?
                    # TODO: Test & implement
                ],
                "chunk_size": page_size,  # Max chunk size
            }
        }

        if _continuation_token:
            request_params["filter"]["continuation_token"] = _continuation_token

        async with aiohttp_session.post(
            rpc_url,
            json=(
                payload := {
                    "jsonrpc": "2.0",
                    "method": "starknet_getEvents",
                    "params": request_params,
                    "id": 1,
                }
            ),
        ) as response:
            events_json = await parse_async_rpc_response(payload, response)
            token = events_json.get("continuation_token")
            return parse_event_response(events_json), token

    events, continuation_token = await _get_page_of_events()

    while continuation_token is not None:
        _events, continuation_token = await _get_page_of_events(continuation_token)
        events.extend(_events)

    return events


async def starknet_call(
    contract_address: bytes,
    entry_point_selector: bytes,
    calldata: list[bytes],
    aiohttp_session: ClientSession,
    rpc_url: str,
    block_id: int | str = "latest",
) -> list[str] | None:
    """
    Call a Starknet contract at a given block number

    :param contract_address:  Contract Address
    :param entry_point_selector:  Selector for the entry point
    :param calldata:  Calldata for the contract call
    :param aiohttp_session:  Async HTTP Client Session
    :param rpc_url:  URL for Starknet RPC
    :param block_id:  Block number to call the contract at.  Defaults to 'latest'
    :return:  Return data from the contract call
    """
    async with aiohttp_session.post(
        rpc_url,
        json={
            "jsonrpc": "2.0",
            "method": "starknet_call",
            "params": {
                "request": {
                    "contract_address": to_hex(contract_address, pad=32),
                    "entry_point_selector": to_hex(entry_point_selector, pad=32),
                    "calldata": [to_hex(data.lstrip(b"\x00")) for data in calldata],
                },
                "block_id": _starknet_block_id(block_id),
            },
            "id": 1,
        },
    ) as response:
        response_json = await response.json()  # Async read response bytes
        response.release()  # Release the connection back to the pool, keeping TCP conn alive

        if "error" in response_json:
            return None
        return response_json["result"]
