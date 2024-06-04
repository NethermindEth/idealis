from typing import Any

from nethermind.idealis.types.ethereum.consensus import BeaconBlock, BlobSidecar
from nethermind.idealis.utils import to_bytes


def parse_signed_beacon_block(signed_block_header: dict[str, Any]) -> BeaconBlock:
    return BeaconBlock(
        slot=int(signed_block_header["message"]["slot"]),
        proposer_index=int(signed_block_header["message"]["proposer_index"]),
        parent_root=to_bytes(signed_block_header["message"]["parent_root"]),
        state_root=to_bytes(signed_block_header["message"]["state_root"]),
        body_root=to_bytes(signed_block_header["message"]["body_root"]),
        signature=to_bytes(signed_block_header["signature"]),
    )


def parse_blob_sidecar_response(
    response_data: list[dict[str, Any]]
) -> tuple[BeaconBlock | None, list[BlobSidecar]]:
    blob_sidecars = []
    beacon_block = None

    for blob_sidecar in response_data:
        if not beacon_block:
            beacon_block = parse_signed_beacon_block(
                blob_sidecar["signed_block_header"]
            )

        blob_sidecars.append(
            BlobSidecar(
                slot=beacon_block.slot,
                blob_index=int(blob_sidecar["index"]),
                blob_data=to_bytes(blob_sidecar["blob"]),
                kzg_commitment=to_bytes(blob_sidecar["kzg_commitment"]),
                kzg_proof=to_bytes(blob_sidecar["kzg_proof"]),
                kzg_commitment_inclusion_proof=[
                    to_bytes(p) for p in blob_sidecar["kzg_commitment_inclusion_proof"]
                ],
            )
        )

    return beacon_block, blob_sidecars
