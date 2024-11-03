from dataclasses import dataclass
from enum import Enum
from typing import Any

from nethermind.idealis.types.base import DataclassDBInterface


class StarknetIDUpdateKind(Enum):
    subdomain_to_address_update = "Subdomain -> Address Update"
    # Basic Update mapping a subdomain without an identity to an address
    # Fields: {domain: str, address: bytes}

    identity_update = "Identity Update"
    # Minting or Transferring Identity NFT & Assigning Domain
    # All data here is tied to an Identity NFT
    # Fields: {id: int, domains: list[tuple[str, int]] | None, new_owner: bytes, old_owner: bytes | None}

    identity_data_update = "Identity Data Update"
    # Adding Verifier or User Data to an Identity NFT
    # Fields: {id: int, verifier_data: dict[str, tuple[list[bytes], bytes], user_data: dict[str, list[bytes]]}


@dataclass(slots=True)
class StarknetIDUpdate(DataclassDBInterface):
    block_number: int
    transaction_index: int
    block_timestamp: int | None
    transaction_hash: bytes | None

    kind: StarknetIDUpdateKind
    data: dict[str, Any]

    # domain_name: str | None
    # updated_resolve_contract: bytes | None  # Updates to the address -> domain resolution
    # identity_nft_update: bytes | None  # Updates to the identity NFT tokenID
    # updated_expire_timestamp: int | None
    # updated_user_data: dict[str, Any] | None
    # updated_verifier_data: dict[str, Any] | None


@dataclass(slots=True)
class StarknetIDDomain(DataclassDBInterface):
    domain_name: str

    resolve_address: bytes
    expire_timestamp: int


@dataclass(slots=True)
class StarknetIDIdentity(DataclassDBInterface):
    identity_nft_id: int

    owner: bytes
    domain: str
    expire: int
    verifier_data: dict[str, Any]  # Discord, Twitter, Eth address, etc
    user_data: dict[str, Any]
