import logging
from typing import Any, Callable, NoReturn

import aiohttp
from aiohttp.client_exceptions import ClientResponse, ContentTypeError
from requests import Response

from nethermind.idealis.exceptions import (
    BlockNotFoundError,
    RPCError,
    RPCHostError,
    RPCRateLimitError,
    RPCTimeoutError,
    StateError,
)

root_logger = logging.getLogger("nethermind")
logger = root_logger.getChild("rpc")

DEFAULT_HEADERS = {"Content-Type": "application/json"}


def create_aiohttp_session(
    max_connections: int = 100,
    max_keepalive: int = 30,
    timeout: int = 60,
) -> aiohttp.ClientSession:
    """
    Create an aiohttp session with the given parameters.

    :param max_connections: Maximum number of connections to allow.
    :param max_keepalive: Maximum number of seconds to keep a connection open.
    :param timeout: Maximum number of seconds to wait for a response.

    :return: aiohttp.ClientSession
    """
    connector = aiohttp.TCPConnector(
        limit=max_connections,
        keepalive_timeout=max_keepalive,
    )

    return aiohttp.ClientSession(
        connector=connector,
        timeout=aiohttp.ClientTimeout(total=timeout),
    )


def handle_rpc_error(response_json: dict[str, Any]) -> None:
    if "error" in response_json.keys():
        logger.debug(f"Error in RPC response: {response_json}")
        raise RPCError("Error in RPC response: " + response_json["error"]["message"])


async def parse_eth_rpc_async_response(
    response: ClientResponse,
) -> Any:
    try:
        response_json = await response.json()  # Async read response bytes
        response.release()  # Release the connection back to the pool, keeping TCP conn alive

        handle_rpc_error(response_json)
        return response_json["result"]

    except ContentTypeError:
        match response.status:
            case 1015 | 429:
                raise RPCRateLimitError("JSON RPC Server Initializing Rate Limits")
            case 500 | 502 | 503 | 504:
                raise RPCHostError("Internal Server Error")

            case _:
                logger.error(f"\n{'-' * 40}")
                logger.error(
                    "Unexpected Error in response for request: ", response.request_info
                )
                logger.error(f"Error Code: {response.status}")
                logger.error(await response.text())
                logger.error("-" * 40)
                raise RPCError("Unexpected Content Type AioHttp Error")
    except TimeoutError:
        raise RPCTimeoutError(f"Timeout Error for RPC Host {response.host}")


async def parse_beacon_api_async_response(
    response: ClientResponse, error_handler: Callable[[str], NoReturn]
):
    match response.status:
        case 200:
            response_json = await response.json()
            response.release()
            return response_json
        case 404:
            response_json = await response.json()
            response.release()
            error_handler(response_json["message"])

        case 500 | 502 | 503 | 504:
            raise Exception("Internal Beacon API Server Error")

        case _:
            logger.error("Unexpected Error in response for request: ", response)
            logger.error(f"Error Code: {response.status}")
            logger.error(await response.text())
            raise NotImplementedError("Unexpected AioHttp Error")


def parse_beacon_api_response(
    response: Response, error_handler: Callable[[str], NoReturn]
):
    match response.status_code:
        case 200:
            return response.json()
        case 404:
            error_handler(response.json()["message"])
        case 500 | 502 | 503 | 504:
            raise Exception("Internal Beacon API Server Error")
        case _:
            logger.error("Unexpected Error in response for request: ", response.request)
            logger.error(f"Error Code: {response.status_code}")
            raise NotImplementedError("Unexpected HTTP Error")


def handle_beacon_api_caplin_errors(error_message: str):
    match error_message.split(" "):
        case ["block", "not", "found", *_]:
            raise BlockNotFoundError("Beacon Slot Not Found")
        case _:
            logger.error("Unknown 404 Error Returned From Caplin Beacon API")
            logger.error("Error Message: ", error_message)
            raise NotImplementedError("Unknown 404 Error Returned From Beacon API")


def handle_beacon_api_lighthouse_errors(error_message: str):
    match error_message.split(" "):
        case ["NOT_FOUND:", "beacon", "state", *_]:
            raise StateError("Beacon State Not Found")
        case ["NOT_FOUND:", "beacon", "block", *_]:
            raise BlockNotFoundError("Beacon Slot Not Found")
        case _:
            logger.error("Unknown 404 Error Returned From Lighthouse Beacon API")
            logger.error("Error Message: ", error_message)
            raise NotImplementedError("Unknown 404 Error Returned From Beacon API")
