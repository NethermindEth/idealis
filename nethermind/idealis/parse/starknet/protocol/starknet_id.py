import logging
from typing import Any

from nethermind.idealis.parse.starknet.event import TRANSFER_SIGNATURE
from nethermind.idealis.types.base import ERC721Transfer
from nethermind.idealis.types.starknet import Event
from nethermind.idealis.types.starknet.protocol.starknet_id import (
    StarknetIDIdentity,
    StarknetIDUpdate,
    StarknetIDUpdateKind,
)
from nethermind.idealis.utils import to_bytes
from nethermind.idealis.utils.starknet.protocol import (
    STARKNET_ID_MAINNET_IDENTITY_CONTRACT,
    STARKNET_ID_MAINNET_NAMING_CONTRACT,
    STARKNET_ID_MAINNET_VERIFIER_CONTRACT,
    decode_starknet_id_domain,
    decode_subdomain,
)
from nethermind.starknet_abi.utils import starknet_keccak

# V0_ADDR_TO_DOMAIN_UPDATE = starknet_keccak(b"domain_to_addr_update")
V1_ADDR_TO_DOMAIN_UPDATE = starknet_keccak(b"addr_to_domain_update")
V2_ADDR_TO_DOMAIN_UPDATE = starknet_keccak(b"AddressToDomainUpdate")

V0_NAMING_DOMAIN_MINT = starknet_keccak(b"starknet_id_update")
V1_NAMING_DOMAIN_MINT = starknet_keccak(b"DomainMint")

V1_IDENTITY_MAIN_ID_UPDATE = starknet_keccak(b"MainIdUpdate")
V1_IDENTITY_VERIFIER_DATA_UPDATE = starknet_keccak(b"VerifierDataUpdate")
V1_IDENTITY_EXTENDED_VERIFIER_DATA_UPDATE = starknet_keccak(b"ExtendedVerifierDataUpdate")
V1_IDENTITY_USER_DATA_UPDATE = starknet_keccak(b"UserDataUpdate")
V1_IDENTITY_EXTENDED_USER_DATA_UPDATE = starknet_keccak(b"ExtendedUserDataUpdate")


root_logger = logging.getLogger("nethermind")
logger = root_logger.getChild("parse").getChild("starknet")


def _starknet_id_defaults(event: Event, skip_keys: set[str]) -> dict[str, Any]:
    event_defaults = {
        "domain_name": None,
        "block_number": event.block_number,
        "transaction_index": event.transaction_index,
        "event_index": event.event_index,
        "block_timestamp": None,
        "transaction_hash": None,
        "identity_nft_update": None,
        "updated_resolve_contract": None,
        "updated_expire_timestamp": None,
        "updated_user_data": None,
        "updated_verifier_data": None,
    }

    return {k: v for k, v in event_defaults.items() if k not in skip_keys}


def _get_addr_to_domain_updates(events: list[Event]) -> list[tuple[bytes, str | None]] | None:
    updates: list[tuple[bytes, str | None]] = []

    for event in events:
        # if event.keys[0] == V0_ADDR_TO_DOMAIN_UPDATE:
        #     _domain_data = [int.from_bytes(b) for b in event.data[1:-1]]
        #     domain = decode_subdomain(_domain_data) if _domain_data else None
        #     updates.append((event.data[-1], domain))
        if event.keys[0] == V1_ADDR_TO_DOMAIN_UPDATE:
            _domain_data = [int.from_bytes(b) for b in event.data[2:]]
            domain = decode_subdomain(_domain_data) if _domain_data else None
            updates.append((event.data[0], domain))
        elif event.keys[0] == V2_ADDR_TO_DOMAIN_UPDATE:
            _domain_data = [int.from_bytes(b) for b in event.data[1:]]
            domain = decode_subdomain(_domain_data) if _domain_data else None
            updates.append((event.keys[1], domain))
        else:
            continue

    return updates if updates else None


def _get_domain_mints(naming_events: list[Event], naming_contract: bytes) -> dict[int, list[tuple[str, int]]] | None:
    # Get DomainMint events, returning ID, domain, and expire

    domain_mints: dict[int, list[tuple[str, int]]] = {}
    for e in naming_events:
        if e.contract_address != naming_contract:
            continue

        if e.keys[0] == V0_NAMING_DOMAIN_MINT:
            domain = decode_starknet_id_domain(int.from_bytes(e.data[1:-2][0], "big"))
            owner = int.from_bytes(e.data[-2], "big")
            expire = int.from_bytes(e.data[-1], "big")

        elif e.keys[0] == V1_NAMING_DOMAIN_MINT:
            domain = decode_starknet_id_domain(int.from_bytes(e.keys[1], "big"))
            owner = int.from_bytes(e.data[0], "big")
            expire = int.from_bytes(e.data[1], "big")

        else:
            continue

        if owner in domain_mints:
            domain_mints[owner].append((domain + ".stark", expire))
        else:
            domain_mints[owner] = [(domain + ".stark", expire)]

    return domain_mints if domain_mints else None


def _get_identity_transfers(events: list[Event], identity_contract: bytes) -> dict[int, list[ERC721Transfer]] | None:
    """
    Given a list of events, get all the Starkent ID Identity transfers, and return a mapping identity IDs to
    transfer events

    :param events:
    :param identity_contract:
    :return:
    """
    id_transfers: dict[int, list[ERC721Transfer]] = {}

    for e in events:
        if e.contract_address != identity_contract or e.keys[0] != TRANSFER_SIGNATURE:
            continue

        shared_params = {
            "block_number": e.block_number,
            "transaction_index": e.transaction_index,
            "event_index": e.event_index,
            "token_address": e.contract_address,
        }

        if len(e.keys) == 5:
            identity_token_id = int.from_bytes(e.keys[3], "big")
            transfer = ERC721Transfer(
                from_address=e.keys[1] if int(e.keys[1].hex(), 16) > 0 else None,
                to_address=e.keys[2] if int(e.keys[2].hex(), 16) > 0 else None,
                token_id=e.keys[3],
                **shared_params,
            )
        elif len(e.keys) == 1 and len(e.data) == 4:
            identity_token_id = int.from_bytes(e.data[2], "big")
            transfer = ERC721Transfer(
                from_address=e.data[0] if int(e.data[0].hex(), 16) > 0 else None,
                to_address=e.data[1] if int(e.data[1].hex(), 16) > 0 else None,
                token_id=e.data[2],
                **shared_params,
            )
        else:
            continue

        if identity_token_id in id_transfers:
            id_transfers[identity_token_id].append(transfer)
        else:
            id_transfers[identity_token_id] = [transfer]

    return id_transfers if id_transfers else None


def _get_main_id_updates(events: list[Event], identity_contract: bytes) -> dict[int, bytes] | None:
    """
    Given a list of events, return a mapping from identity -> owner address.  If an id already exists, it is overridden
    :param events:
    :param identity_contract:
    :return:
    """
    main_id_updates = {}
    sorted_events = sorted(events, key=lambda e: (e.block_number, e.transaction_index, e.event_index))
    for e in sorted_events:
        if e.contract_address != identity_contract:
            continue

        if e.keys[0] == V1_IDENTITY_MAIN_ID_UPDATE:
            main_id_updates[int.from_bytes(e.data[0], "big")] = e.keys[1]

    return main_id_updates if main_id_updates else None


def _get_identity_verifier_data(
    events: list[Event], identity_contract: bytes
) -> dict[int, dict[str, tuple[list[bytes], bytes]]] | None:
    verifier_data: dict[int, dict[str, tuple[list[bytes], bytes]]] = {}

    for e in events:
        if e.contract_address != identity_contract:
            continue

        if e.keys[0] == V1_IDENTITY_VERIFIER_DATA_UPDATE:
            if len(e.keys) == 2:
                identity_id = int.from_bytes(e.keys[1], "big")
                field = e.data[0].decode("utf-8")
                data = [e.data[1]]
                verifier_contract = e.data[2]
            else:
                identity_id = int.from_bytes(e.data[0], "big")
                field = e.data[1].decode("utf-8")
                data = [e.data[2]]
                verifier_contract = e.data[3]

        elif e.keys[0] == V1_IDENTITY_EXTENDED_VERIFIER_DATA_UPDATE:
            identity_id = int.from_bytes(e.keys[1], "big")
            field = e.data[0].decode("utf-8")
            data = e.data[2:-1]
            verifier_contract = e.data[-1]

        else:
            continue

        if identity_id in verifier_data:
            verifier_data[identity_id][field] = (data, verifier_contract)
        else:
            verifier_data[identity_id] = {field: (data, verifier_contract)}

    return verifier_data if verifier_data else None


def _get_identity_user_data(events: list[Event], identity_contract: bytes) -> dict[int, dict[str, list[bytes]]] | None:
    user_data: dict[int, dict[str, list[bytes]]] = {}

    for e in events:
        if e.contract_address != identity_contract:
            continue

        if e.keys[0] == V1_IDENTITY_USER_DATA_UPDATE:
            identity_id = int.from_bytes(e.keys[1], "big")
            field = e.data[0].decode("utf-8")
            data = [e.data[1]]

        elif e.keys[0] == V1_IDENTITY_EXTENDED_USER_DATA_UPDATE:
            identity_id = int.from_bytes(e.keys[1], "big")
            field = e.data[0].decode("utf-8")
            data = e.data[2:]

        else:
            continue

        if identity_id in user_data:
            user_data[identity_id][field] = data
        else:
            user_data[identity_id] = {field: data}

    return user_data if user_data else None


def parse_starknet_id_updates(
    events: list[Event],
    naming_contract: bytes = STARKNET_ID_MAINNET_NAMING_CONTRACT,
    identity_contract: bytes = STARKNET_ID_MAINNET_IDENTITY_CONTRACT,
    verifier_contract: bytes = STARKNET_ID_MAINNET_VERIFIER_CONTRACT,
) -> list[StarknetIDUpdate]:
    starknet_id_updates = []

    grouped_events: dict[tuple[int, int], list[Event]] = {}

    for e in events:
        if not e.contract_address in {naming_contract, identity_contract, verifier_contract}:
            continue

        tx_key = (e.block_number, e.transaction_index)
        if tx_key in grouped_events:
            grouped_events[tx_key].append(e)
        else:
            grouped_events[tx_key] = [e]

    sorted_keys = sorted(grouped_events.keys())

    for update_tx in sorted_keys:
        try:
            update_events = grouped_events[update_tx]
            update_params = {
                "block_number": update_tx[0],
                "transaction_index": update_tx[1],
                "block_timestamp": None,
                "transaction_hash": None,
            }

            # Simple Subdomain Registration
            _domain_to_address_updates = _get_addr_to_domain_updates(update_events)
            if _domain_to_address_updates:
                updates = {}
                for address, domain in _domain_to_address_updates:
                    updates[domain] = address

                for domain, address in updates.items():
                    starknet_id_updates.append(
                        StarknetIDUpdate(
                            identity=address,
                            kind=StarknetIDUpdateKind.address_to_domain_update,
                            data={"domain": domain, "address": address},
                            **update_params,  # type: ignore
                        )
                    )

            # Domain Identity Update -- All updates tied to a Identity Token ID
            _id_transfers = _get_identity_transfers(update_events, identity_contract)
            _domain_mints = _get_domain_mints(update_events, naming_contract)
            _main_id_updates = _get_main_id_updates(update_events, identity_contract)
            if _id_transfers or _domain_mints or _main_id_updates:
                distinct_ids = set(_id_transfers or {}).union(_domain_mints or {}).union(_main_id_updates or {})

                for _id in distinct_ids:
                    transfers = _id_transfers.get(_id, []) if _id_transfers else []
                    mints = _domain_mints.get(_id) if _domain_mints else None
                    id_owner_change = _main_id_updates.get(_id) if _main_id_updates else None

                    transfer_to = transfers[-1].to_address if transfers else None
                    transfer_from = transfers[-1].from_address if transfers else None
                    if transfer_from == to_bytes("00", pad=32):
                        transfer_from = None

                    starknet_id_updates.append(
                        StarknetIDUpdate(
                            identity=_id.to_bytes(32, "big"),
                            kind=StarknetIDUpdateKind.identity_update,
                            data={
                                "domains": mints,
                                "new_owner": transfer_to or id_owner_change,
                                "old_owner": transfer_from,
                            },
                            **update_params,  # type: ignore
                        )
                    )

            # Identity User & Verifier Data Update
            _verifier_data = _get_identity_verifier_data(update_events, identity_contract)
            _user_data = _get_identity_user_data(update_events, identity_contract)

            if _verifier_data or _user_data:
                unique_ids = set(_verifier_data or {}).union(_user_data or {})

                for _id in unique_ids:
                    verifier_data = _verifier_data.get(_id) if _verifier_data else None
                    user_data = _user_data.get(_id) if _user_data else None

                    starknet_id_updates.append(
                        StarknetIDUpdate(
                            identity=_id.to_bytes(32, "big"),
                            kind=StarknetIDUpdateKind.identity_data_update,
                            data={"verifier_data": verifier_data, "user_data": user_data},
                            **update_params,  # type: ignore
                        )
                    )

        except Exception as e:
            logger.error(f"Error parsing StarknetID Update Tx {update_tx}: {e}")
            continue

    return starknet_id_updates


def enrich_starknet_id_updates(
    updates: list[StarknetIDUpdate], transaction_data: dict[tuple[int, int], tuple[int, bytes]]
) -> list[StarknetIDUpdate]:
    """
    Enrich starknet ID Updates with block timestamp & transaction hash.  Requires a tx position hashmap with block
    timestamp & tx hash data

    :param updates:  List of Starknet ID Updates
    :param transaction_data: Dictionary between (block_num, tx_idx) -> (block_timestamp, tx_hash)
    """
    for update in updates:
        tx_data = transaction_data.get((update.block_number, update.transaction_index))
        if tx_data is None:
            continue

        update.block_timestamp = tx_data[0]
        update.transaction_hash = tx_data[1]

    return updates


def generate_starknet_id_state(
    identity_state: dict[int, StarknetIDIdentity],
    address_to_domain: dict[bytes, str],
    address_to_identity: dict[bytes, int],
    starknet_id_updates: list[StarknetIDUpdate],
) -> tuple[dict[int, StarknetIDIdentity], dict[bytes, str], dict[bytes, int]]:
    """
    Generate Starknet ID State from a list of ordered updates
    :param identity_state: State of Identity NFTS, mapping identities to user data & domains
    :param address_to_domain: State of Address Resolution, mapping addresses to domain names
    :param address_to_identity: State of Addresses to Identity NFTs
    :param starknet_id_updates: Sorted list of StarknetID Updates
    :return:
    """

    # TODO: Handle sorting better.  When minting ID & adding data in same tx, need to place mint first
    sorted_id_updates = sorted(starknet_id_updates, key=lambda u: (u.block_number, u.transaction_index))

    for update in sorted_id_updates:
        match update.kind:
            case StarknetIDUpdateKind.address_to_domain_update:
                if update.data["domain"] is None:
                    address_to_domain.pop(update.data["address"])
                else:
                    address_to_domain[update.data["address"]] = update.data["domain"]

            case StarknetIDUpdateKind.identity_update:
                token_id = int.from_bytes(update.identity, "big")
                existing_identity = identity_state.get(token_id)

                # Updating Existing Identity NFT With new Domain or Owner
                if existing_identity:
                    if update.data["domains"] is not None:
                        for domain_name, domain_expire in update.data["domains"]:
                            pass
                            # TODO: Handle multi domains per ID cases better...

                    if update.data["new_owner"]:
                        existing_identity.owner = update.data["new_owner"]
                        address_to_identity[update.data["new_owner"]] = token_id

                # Minting New Identity NFT & Setting Domain & User Data
                else:
                    identity_state[token_id] = StarknetIDIdentity(
                        identity_nft_id=token_id,
                        owner=update.data["new_owner"],
                        domain=update.data["domains"][0][0],  # TODO: Handle multi domains per ID cases better...
                        expire=update.data["domains"][0][1],
                        verifier_data={},
                        user_data={},
                    )
                    address_to_identity[update.data["new_owner"]] = token_id

            case StarknetIDUpdateKind.identity_data_update:
                token_id = int.from_bytes(update.identity, "big")

                if token_id not in identity_state:
                    raise ValueError(f"Cannot add Data to Nonexistent Identity {token_id}")

                new_verifier_data, new_user_data = update.data["verifier_data"], update.data["user_data"]
                identity = identity_state[token_id]

                if new_verifier_data:
                    identity.verifier_data.update(new_verifier_data)

                if new_user_data:
                    identity.user_data.update(new_user_data)

    return identity_state, address_to_domain, address_to_identity
