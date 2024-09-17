from typing import Any

from nethermind.idealis.types.base import ERC20Transfer, ERC721Transfer
from nethermind.idealis.types.starknet.core import Event
from nethermind.idealis.utils import to_bytes
from nethermind.starknet_abi.utils import starknet_keccak

TRANSFER_SIGNATURE = starknet_keccak(b"Transfer")


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
        match sorted_keys:
            # -----------------------------------------
            # ERC20 Transfer Cases
            # -----------------------------------------

            case ("from", "to", "value") | ("from_", "to", "value") | ("amount", "from", "to"):
                # Standard ERC20 transfers
                erc_20_transfers.append(
                    ERC20Transfer(
                        from_address=event.decoded_params.get("from") or event.decoded_params["from_"],
                        to_address=event.decoded_params["to"],
                        value=event.decoded_params.get("value") or event.decoded_params["amount"],
                        **shared_params,  # type: ignore
                    )
                )

            case ("counter", "from", "to", "value"):
                erc_20_transfers.append(
                    ERC20Transfer(
                        from_address=event.decoded_params["from"],
                        to_address=event.decoded_params["to"],
                        value=event.decoded_params["value"],
                        **shared_params,  # type: ignore
                    )
                )

            case ("amount", "from_address", "to_address"):
                erc_20_transfers.append(
                    ERC20Transfer(
                        from_address=event.decoded_params["from_address"],
                        to_address=event.decoded_params["to_address"],
                        value=event.decoded_params["amount"],
                        **shared_params,  # type: ignore
                    )
                )

            case ("recipient", "sender", "value"):
                erc_20_transfers.append(
                    ERC20Transfer(
                        from_address=event.decoded_params["sender"],
                        to_address=event.decoded_params["recipient"],
                        value=event.decoded_params["value"],
                        **shared_params,  # type: ignore
                    )
                )

            # -----------------------------------------
            # ERC721 Transfer Cases
            # -----------------------------------------

            case ("from", "to", "token_id"):  # Standard ERC721 transfers
                erc_721_transfers.append(
                    ERC721Transfer(
                        from_address=event.decoded_params["from"],
                        to_address=event.decoded_params["to"],
                        token_id=event.decoded_params["token_id"],
                        **shared_params,  # type: ignore
                    )
                )
            case ("_from", "_to", "_tokenId") | ("_from", "to", "tokenId") | ("from_", "to", "tokenId"):
                erc_721_transfers.append(
                    ERC721Transfer(
                        from_address=event.decoded_params.get("_from") or event.decoded_params["from_"],
                        to_address=event.decoded_params.get("to") or event.decoded_params["_to"],
                        token_id=event.decoded_params.get("tokenId") or event.decoded_params["_tokenId"],
                        **shared_params,  # type: ignore
                    )
                )
            case _:
                continue

    return erc_20_transfers, erc_721_transfers
