from dataclasses import dataclass
from enum import Enum
from typing import Any

from nethermind.idealis.types.base import DataclassDBInterface


class StarknetIDUpdateKind(Enum):
    address_to_domain_update = "Address -> Domain Update"
    # Basic Update mapping an address to a domain or subdomain.  Ignores Identity NFTs & larger starknet ID system
    # Fields: {domain: str | None, address: bytes}

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

    identity: bytes  # byte repr of the token id, or starknet_keccak of utf-8 encoded domain name
    kind: StarknetIDUpdateKind
    data: dict[str, Any]


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
