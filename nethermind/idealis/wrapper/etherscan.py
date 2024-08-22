import logging
from typing import Any

import requests

from nethermind.idealis.types.ethereum import Transaction
from nethermind.idealis.utils import to_bytes

root_logger = logging.getLogger("nethermind")
logger = root_logger.getChild("entro").getChild("backfill").getChild("etherscan")


# janky...  Fix later if etherscan API is implemented on other chains


def _validate_api_key(key: str | None) -> str:
    if key is None:
        raise ValueError("API key is required for Etherscan backfill")

    if len(key) != 34:
        raise ValueError("Etherscan API keys are 34 characters long.  Double check --api-key")

    return key


def handle_etherscan_error(response: requests.Response) -> Any:
    """
    Check status codes and Response parameters before returning the json result from API
    :param response: requests.Response object
    :return: respone.json()['result']
    """
    match response.status_code:
        case 200:
            response_data = response.json()
            if response_data.get("status") == "1":
                return response_data["result"]

            # Error Handling Section
            match response_data["message"]:
                case "Missing/Invalid API Key":
                    raise ValueError("Invalid Etherscan API Key")
                case _:
                    raise RuntimeError("Unhandled Etherscan Error: " + response_data)
        case _:
            raise ConnectionError(
                f"Unexpected Response Status Code ({response.status_code}) for Etherscan API. "
                f"Response Data: {response}"
            )


# pylint: disable=too-many-locals
def get_transactions_for_account(
    api_key: str, api_endpoint: str, from_block: int, to_block: int, account_address: bytes, page_size: int = 1000
):
    output_transactions = []
    search_block = from_block

    # This fucked loop is implemented since the paged API only returns a max of
    # 10,000 transactions, requiring overflow logic regardless...
    while True:
        response = requests.get(
            api_endpoint,
            params={  # type: ignore
                "module": "account",
                "action": "txlist",
                "address": "0x" + account_address.hex(),
                "startblock": search_block,
                "endblock": to_block,
                "page": 1,
                "offset": page_size,
                "sort": "asc",
                "apikey": api_key,
            },
            timeout=300,
        )
        raw_tx_batch = handle_etherscan_error(response)

        logger.debug(
            f"Queried {len(raw_tx_batch)} Txns from blocks {raw_tx_batch[0]['blockNumber']} "
            f"- {raw_tx_batch[-1]['blockNumber']}"
        )

        break_loop = len(raw_tx_batch) < page_size

        parsed_transactions = _parse_etherscan_transactions(
            tx_batch=raw_tx_batch if break_loop else _trim_last_block(raw_tx_batch)
        )

        output_transactions.extend(parsed_transactions)

        if break_loop:
            logger.info(f"Fetched {len(parsed_transactions)} Transactions from Etherscan API")
            return output_transactions

        search_block = int(parsed_transactions[-1].block_number) + 1


def _trim_last_block(tx_batch: list[dict[str, Any]]) -> list[dict[str, Any]]:
    last_block = int(tx_batch[-1]["blockNumber"])
    slice_index = -1
    while True:
        slice_index -= 1
        current_block = int(tx_batch[slice_index]["blockNumber"])
        if current_block != last_block:
            return tx_batch[: slice_index + 1]


def _parse_etherscan_transactions(
    tx_batch: list[dict[str, Any]],
) -> list[Transaction]:
    return [
        Transaction(
            block_number=int(tx_data["blockNumber"]),
            transaction_hash=to_bytes(tx_data["hash"], pad=32),
            transaction_index=int(tx_data["transactionIndex"]),
            timestamp=int(tx_data["timeStamp"]),
            nonce=int(tx_data["nonce"]),
            type=None,
            value=int(tx_data["value"]),
            gas_price=int(tx_data["gasPrice"]),
            gas_supplied=int(tx_data["gas"]),
            gas_used=int(tx_data["gasUsed"]),
            max_priority_fee=None,
            max_fee=None,
            to_address=to_bytes(tx_data["to"], pad=20) if tx_data["to"] else None,
            from_address=to_bytes(tx_data["from"], pad=20),
            input=to_bytes(tx_data["input"]),
            decoded_input=None,
            function_name=None if tx_data["functionName"] == "" else tx_data["functionName"].rsplit("(", 1)[0],
        )
        for tx_data in tx_batch
    ]
