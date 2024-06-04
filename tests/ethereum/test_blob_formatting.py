import pytest

from nethermind.idealis.rpc.ethereum.consensus_parsing import (
    parse_blob_sidecar_response,
    parse_signed_beacon_block,
)
from tests.utils import load_rpc_response


def test_parse_signed_block_header():
    signed_block_header = {
        "message": {
            "slot": "7785423",
            "proposer_index": "610832",
            "parent_root": "0xd48946a1854b1f8a02178cc71cff5574ceff4d34354405a851168a21739ae1c8",
            "state_root": "0xbf8ac74a7fd177b11a96d4aace6c697b9a069f80e030eb0f9a75cb0960abd8e4",
            "body_root": "0x69b2e5a28174473dfbdbbcdb567947a2596efe7ef7ac32de2debaf8fa16e77f6",
        },
        "signature": "0x8dea8bd658d961460735ff76023cf3166b674004d6050b060ee6e26f0a0710c907a496ff76f755ba0655603e3f71744b1675ebc0446550dc342c449e13c6cc35deef28d28f254f2feef036d0a550bc690c963c17304bb57e71be7647db4044ce",
    }

    beacon_block = parse_signed_beacon_block(signed_block_header)

    assert beacon_block.slot == 7785423
    assert beacon_block.proposer_index == 610832
    assert beacon_block.parent_root == bytes.fromhex("d48946a1854b1f8a02178cc71cff5574ceff4d34354405a851168a21739ae1c8")
    assert beacon_block.signature[:32] == bytes.fromhex(
        "8dea8bd658d961460735ff76023cf3166b674004d6050b060ee6e26f0a0710c9"
    )


def test_blob_formatting():
    blob_sidecar_response = load_rpc_response("ethereum", "beacon_get_blob_sidecars.json")

    beacon_block, blob_sidecars = parse_blob_sidecar_response(blob_sidecar_response["data"])

    assert beacon_block.slot == 7785423
    assert beacon_block.proposer_index == 610832

    assert len(blob_sidecars) == 6

    for blob_sidecar in blob_sidecars:
        assert blob_sidecar.slot == 7785423
