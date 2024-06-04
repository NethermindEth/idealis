from dataclasses import dataclass

from nethermind.idealis.types.base import DataclassDBInterface

# class BeaconVersion(Enum):
#     phase0 = "phase0"
#     altair = "altair"
#     bellatrix = "bellatrix"
#     capella = "capella"
#     deneb = "deneb"


@dataclass
class BeaconBlock:
    slot: int
    proposer_index: int
    parent_root: bytes
    state_root: bytes
    body_root: bytes
    signature: bytes


@dataclass
class BlobSidecar(DataclassDBInterface):
    slot: int
    blob_index: int
    blob_data: bytes
    kzg_commitment: bytes
    kzg_proof: bytes
    kzg_commitment_inclusion_proof: list[bytes]
