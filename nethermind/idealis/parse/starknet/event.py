from typing import Any

from nethermind.idealis.types.starknet.core import Event
from nethermind.idealis.types.starknet.tokens import ERC20Transfer, ERC721Transfer
from nethermind.idealis.utils import to_bytes
from nethermind.starknet_abi.utils import starknet_keccak

TRANSFER_SIGNATURE = starknet_keccak(b"Transfer")


def parse_event_response(rpc_response: dict[str, Any]) -> list[Event]:
    events = rpc_response["events"]

    return [
        Event(
            block_number=e["block_number"],
            tx_index=-1,
            event_index=-1,
            contract_address=to_bytes(e["from_address"], pad=32),
            class_hash=None,
            keys=[to_bytes(k, pad=32) for k in e["keys"]],
            data=[to_bytes(d) for d in e["data"]],
        )
        for e in events
    ]


def filter_erc_20_transfers(events: list[Event]) -> list[ERC20Transfer]:
    """
    Filter out ERC20 Transfer events from a list of Starknet Events
    """

    return [
        ERC20Transfer(
            block_number=event.block_number,
            transaction_index=event.tx_index,
            event_index=event.event_index,
            token_address=event.contract_address,
            from_address=event.decoded_params["from_"],
            to_address=event.decoded_params["to"],
            value=event.decoded_params["value"],
        )
        for event in events
        if len(event.keys) > 0
        and event.keys[0] == TRANSFER_SIGNATURE
        and event.decoded_params is not None
        and "value" in event.decoded_params
        and "from_" in event.decoded_params
        and "to" in event.decoded_params
    ]


def filter_erc_721_transfers(events: list[Event]) -> list[ERC721Transfer]:
    """
    Filter out ERC721 Transfer events from a list of Starknet Events
    """

    return [
        ERC721Transfer(
            block_number=event.block_number,
            transaction_index=event.tx_index,
            event_index=event.event_index,
            token_address=event.contract_address,
            from_address=event.decoded_params["from_"],
            to_address=event.decoded_params["to"],
            token_id=event.decoded_params["tokenId"],
        )
        for event in events
        if len(event.keys) > 0
        and event.keys[0] == TRANSFER_SIGNATURE
        and event.decoded_params is not None
        and "tokenId" in event.decoded_params
        and "from_" in event.decoded_params
        and "to" in event.decoded_params
    ]
