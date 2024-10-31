from nethermind.starknet_abi.utils import starknet_keccak

from nethermind.idealis.types.starknet import Event
from nethermind.idealis.types.starknet.protocol.starknet_id import StarknetIDUpdate, StarknetID
from nethermind.idealis.utils import to_bytes

from nethermind.idealis.utils.starknet.protocol import (
    STARKNET_ID_MAINNET_NAMING_CONTRACT,
    STARKNET_ID_MAINNET_VERIFIER_CONTRACT,
    STARKNET_ID_MAINNET_IDENTITY_CONTRACT,
    encode_starknet_id_domain,
    decode_starknet_id_domain, decode_subdomain,
)

V0_ADDR_TO_DOMAIN_UPDATE = starknet_keccak(b"addr_to_domain_update")
V1_ADDR_TO_DOMAIN_UPDATE = starknet_keccak(b"AddressToDomainUpdate")

V0_NAMING_DOMAIN_MINT = starknet_keccak(b"starknet_id_update")
V1_NAMING_DOMAIN_MINT = starknet_keccak(b"DomainMint")


def _handle_naming_updates(event: Event) -> StarknetIDUpdate | None:
    # Handle Reverse Contract -> Domain resolving update events
    if event.keys[0] == V0_ADDR_TO_DOMAIN_UPDATE:
        return StarknetIDUpdate(
            domain_name=decode_subdomain([int.from_bytes(b) for b in event.data[2:]]),
            block_number=event.block_number,
            transaction_index=event.transaction_index,
            event_index=event.event_index,
            block_timestamp=None,
            transaction_hash=None,
            updated_resolve_contract=event.data[0],
            owner_update=None,
            updated_expire_timestamp=None,
            updated_user_data=None,
            updated_verifier_data=None,
        )

    if event.keys[0] == V1_ADDR_TO_DOMAIN_UPDATE:
        return StarknetIDUpdate(
            domain_name=decode_subdomain([int.from_bytes(b) for b in event.data[1:]]),
            block_number=event.block_number,
            transaction_index=event.transaction_index,
            event_index=event.event_index,
            block_timestamp=None,
            transaction_hash=None,
            updated_resolve_contract=event.keys[1],
            owner_update=None,
            updated_expire_timestamp=None,
            updated_user_data=None,
            updated_verifier_data=None,
        )


    # Handle Domain Mints & Registrations
    if event.keys[0] == V0_NAMING_DOMAIN_MINT:
        domain = event.data[1:-3]
        owner = event.data[-2]
        expire = int.from_bytes(event.data[-1], 'big')

    elif event.keys[0] == V1_NAMING_DOMAIN_MINT:
        domain = [event.keys[1]]
        owner = event.data[0]
        expire = int.from_bytes(event.data[1], 'big')
    else:
        domain, owner, expire = None, None, None


def parse_starknet_id_updates(
    events: list[Event],
    naming_contract: bytes = STARKNET_ID_MAINNET_NAMING_CONTRACT,
    identity_contract: bytes = STARKNET_ID_MAINNET_IDENTITY_CONTRACT,
    verifier_contract: bytes = STARKNET_ID_MAINNET_VERIFIER_CONTRACT,
) -> list[StarknetIDUpdate]:
    starknet_id_updates = []

    for event in events:
        if event.contract_address not in {naming_contract, identity_contract, verifier_contract}:
            continue

        if event.contract_address == STARKNET_ID_MAINNET_NAMING_CONTRACT:
            update = _handle_naming_updates(event)
            if update:
                starknet_id_updates.append(update)
            continue

        if event.contract_address == STARKNET_ID_MAINNET_IDENTITY_CONTRACT:
            continue

    return starknet_id_updates


def generate_starknet_ids(
    starknet_id_state: dict[str, StarknetID],
    id_updates: list[StarknetIDUpdate]
) -> dict[str, StarknetID]:
    """
    Generate Starknet ID State from a list of ordered updates
    :param starknet_id_state: State of Starknet IDs and resolve addresses
    :param id_updates: Sorted list of StarknetID Updates
    :return:
    """
    for update in id_updates:

        if update.domain_name not in starknet_id_state:
            starknet_id_state[update.domain_name] = StarknetID(
                domain_name=update.domain_name,
                owner_address=update.owner_update,
                resolve_address=update.updated_resolve_contract,
                expire_timestamp=update.updated_expire_timestamp,
                verifier_data=update.updated_verifier_data or {},  # Discord, Twitter, Eth address, etc
                user_data=update.updated_user_data or {},
            )

        else:
            if update.updated_resolve_contract:
                starknet_id_state[update.domain_name].resolve_address = update.updated_resolve_contract
            if update.owner_update:
                starknet_id_state[update.domain_name].owner_address = update.owner_update
            if update.updated_expire_timestamp:
                starknet_id_state[update.domain_name].expire_timestamp = update.updated_expire_timestamp
            if update.updated_user_data:
                starknet_id_state[update.domain_name].user_data.update(update.updated_user_data)
            if update.updated_verifier_data:
                starknet_id_state[update.domain_name].verifier_data.update(update.updated_verifier_data)

    return starknet_id_state


