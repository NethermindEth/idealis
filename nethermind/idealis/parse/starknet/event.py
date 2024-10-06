import logging
from typing import Any

from nethermind.idealis.types.base import ERC20Transfer, ERC721Transfer
from nethermind.idealis.types.starknet.core import Event
from nethermind.idealis.utils import to_bytes, hex_to_int
from nethermind.starknet_abi.utils import starknet_keccak

TRANSFER_SIGNATURE = starknet_keccak(b"Transfer")


root_logger = logging.getLogger("nethermind")
logger = root_logger.getChild("parse").getChild("starknet").getChild("events")


def parse_event_response(rpc_response: dict[str, Any]) -> list[Event]:
    events = rpc_response["events"]

    return [
        Event(
            block_number=e["block_number"],
            transaction_index=-1,
            event_index=-1,
            contract_address=to_bytes(e["from_address"], pad=32),
            class_hash=None,
            keys=[to_bytes(k, pad=32) for k in e["keys"]],
            data=[to_bytes(d) for d in e["data"]],
        )
        for e in events
    ]


# -------------------------------------
# Unhandled starknet transfer events...
# -------------------------------------
# {to,from,amountOrId}  -- Not handled.  WTF? :face_palm:
# {to,ext,token,amount}  -- Not handled  What is ext?
# {id,amount,caller,sender,receiver}  -- Not handled.  1155
# {to,from,asset,amount}  -- Not handled.  Multi ERC Contract?
# {id,to,amount,exp_time}  -- Not handled.  WTF?  Where is the from_address?
# {to,from,tick,value}  -- Not handled.  WTF?


def filter_transfers(events: list[Event]) -> tuple[list[ERC20Transfer], list[ERC721Transfer]]:
    """
    Filter out ERC20 Transfer events from a list of Starknet Events
    """
    erc_20_transfers, erc_721_transfers = [], []

    for event in events:
        if not event.keys or not event.decoded_params or event.keys[0] != TRANSFER_SIGNATURE:
            continue

        shared_params = {
            "block_number": event.block_number,
            "transaction_index": event.transaction_index,
            "event_index": event.event_index,
            "token_address": event.contract_address,
        }
        sorted_keys = tuple(sorted(event.decoded_params.keys()))

        try:
            match sorted_keys:
                # -----------------------------------------
                # ERC20 Transfer Cases
                # -----------------------------------------

                case (
                    ["from", "to", "value"]
                    | ["from_", "to", "value"]
                    | ["amount", "from", "to"]
                    | ["from", "tick", "to", "value"]
                    | ["amount", "asset", "from", "to"]
                    | ["counter", "from", "to", "value"]
                    | ["amount", "from_address", "to_address"]
                    | ["recipient", "sender", "value"]
                ):
                    from_addr = (
                        event.decoded_params.get("from") or
                        event.decoded_params.get("from_") or
                        event.decoded_params.get("from_address") or
                        event.decoded_params.get("sender")
                    )
                    to_addr = (
                        event.decoded_params.get("to") or
                        event.decoded_params.get("to_address") or
                        event.decoded_params.get("recipient")
                    )
                    val = (
                        event.decoded_params.get("value") or
                        event.decoded_params.get("amount")
                    )

                    if isinstance(val, (int, float)):
                        transfer_value = int(val)
                    elif isinstance(val, str):
                        transfer_value = hex_to_int(val)
                    else:
                        transfer_value = None

                    if (
                        (from_addr is None or not isinstance(from_addr, str)) or    # from check
                        (to_addr is None or not isinstance(to_addr, str)) or        # to check
                        transfer_value is None                                                 # value check
                    ):
                        logger.warning(f"Could not parse starknet event into ERC20 Transfer event:  {event}")
                        continue

                    erc_20_transfers.append(
                        ERC20Transfer(
                            from_address=to_bytes(from_addr, pad=32),
                            to_address=to_bytes(to_addr, pad=32),
                            value=transfer_value,
                            **shared_params,  # type: ignore
                        )
                    )

                # -----------------------------------------
                # ERC721 Transfer Cases
                # -----------------------------------------

                case (
                    ["_from", "_to", "_tokenId"]
                    | ["_from", "to", "tokenId"]
                    | ["from_", "to", "tokenId"]
                    | ["from", "to", "token_id"]
                ):  # ERC721 transfers

                    token_id = (
                        event.decoded_params.get("token_id") or
                        event.decoded_params.get("tokenId") or
                        event.decoded_params["_tokenId"]
                    )

                    from_addr = (
                        event.decoded_params.get("_from") or
                        event.decoded_params.get("from_") or
                        event.decoded_params["from"]
                    )

                    to_addr = (
                        event.decoded_params.get("_to") or
                        event.decoded_params["to"]
                    )

                    if isinstance(token_id, str):
                        token_id_bytes = to_bytes(token_id)
                    elif isinstance(token_id, int):
                        token_id_bytes = token_id.to_bytes(32, "big")
                        token_id_bytes = token_id_bytes.lstrip(b"\x00")
                    else:
                        logger.warning(f"Unknown ERC721 Event.  Cannot parse token_id into bytes: {event}")
                        continue

                    erc_721_transfers.append(
                        ERC721Transfer(
                            from_address=to_bytes(from_addr, pad=32),
                            to_address=to_bytes(to_addr, pad=32),
                            token_id=token_id_bytes,
                            **shared_params,  # type: ignore
                        )
                    )

                case _:
                    continue

        except KeyError as e:
            raise ValueError(f"Failed to Parse Transfer Event {event.decoded_params} with KeyError: {e}")

    return erc_20_transfers, erc_721_transfers
