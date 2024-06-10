import logging
from typing import Callable, NoReturn

import requests
from aiohttp import ClientSession

from nethermind.idealis.exceptions import BlockNotFoundError
from nethermind.idealis.rpc.base.async_rpc import (
    parse_beacon_api_async_response,
    parse_beacon_api_response,
)
from nethermind.idealis.rpc.ethereum.consensus_parsing import (
    parse_blob_sidecar_response,
)
from nethermind.idealis.types.ethereum.consensus import BeaconBlock, BlobSidecar

root_logger = logging.getLogger("nethermind")
logger = root_logger.getChild("rpc").getChild("ethereum").getChild("consensus")


async def get_current_slot(
    beacon_api: str,
    session: ClientSession,
    error_handler: Callable[[str], NoReturn],
) -> int | None:
    logger.debug("Async GET Beacon-Chain Head")
    async with session.get(f"{beacon_api}/eth/v1/beacon/headers") as response:
        try:
            block_header = await parse_beacon_api_async_response(response, error_handler)
            return int(block_header["data"][0]["header"]["message"]["slot"])
        except BlockNotFoundError:
            return None


def sync_get_current_slot(beacon_api: str, error_handler: Callable[[str], NoReturn]) -> int | None:
    """
    Get the current slot from the beacon chain.  If Block Not Found Error occurs, returns None

    :param beacon_api:
    :param error_handler:
    :return:
    """
    response = requests.get(f"{beacon_api}/eth/v1/beacon/headers")
    logger.debug(f"Sync GET Request -- Beacon-Chain Head Returned {len(response.content)} bytes")

    try:
        block_header = parse_beacon_api_response(response, error_handler)
        return int(block_header["data"][0]["header"]["message"]["slot"])

    except BlockNotFoundError:
        return None


async def get_beacon_block(
    slot: int,
    beacon_api_url: str,
    aiohttp_session: ClientSession,
    error_handler: Callable[[str], NoReturn],
) -> tuple[BeaconBlock | None, list[BlobSidecar]]:
    logger.debug(f"Requesting Beacon Block for slot {slot}")

    async with aiohttp_session.get(
        url=f"{beacon_api_url}/eth/v1/beacon/blob_sidecars/{slot}",
    ) as response:
        try:
            response_json = await parse_beacon_api_async_response(response, error_handler)
            logger.debug(f"Finished Reading HTTP Response Bytes & Decoding JSON for Beacon Block {slot}")

            return parse_blob_sidecar_response(response_json["data"])

        except BlockNotFoundError:
            logger.debug(f"Beacon Block & Blob Sidecars Not Found for Slot {slot}")
            return None, []


def sync_get_beacon_block(
    slot: int,
    beacon_api_url: str,
    error_handler: Callable[[str], NoReturn],
) -> tuple[BeaconBlock | None, list[BlobSidecar]]:
    response = requests.get(f"{beacon_api_url}/eth/v1/beacon/blob_sidecars/{slot}")
    logger.debug(f"Sync GET -- beacon block {slot} returned {len(response.content)} bytes")

    try:
        response_json = parse_beacon_api_response(response, error_handler)
        return parse_blob_sidecar_response(response_json["data"])

    except BlockNotFoundError:
        return None, []
