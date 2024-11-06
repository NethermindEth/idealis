import pytest

from nethermind.idealis.parse.starknet.protocol.starknet_id import (
    generate_starknet_id_state,
    parse_starknet_id_updates,
)
from nethermind.idealis.rpc.starknet import get_blocks_with_txns
from nethermind.idealis.types.starknet import Event
from nethermind.idealis.types.starknet.protocol.starknet_id import StarknetIDUpdateKind
from nethermind.idealis.utils import to_bytes
from nethermind.idealis.utils.starknet import (
    decode_starknet_id_domain,
    encode_starknet_id_domain,
)
from nethermind.starknet_abi.utils import starknet_keccak


def test_starknet_id_domain_encoding():
    assert encode_starknet_id_domain("nethermind") == 553122413236441
    assert encode_starknet_id_domain("nethermind.stark") == 553122413236441


def test_starknet_id_domain_decoding():
    assert decode_starknet_id_domain(553122413236441) == "nethermind"


def test_parse_starknet_id_subdomain():
    # Test for Braavos Subdomain
    # https://voyager.online/tx/0x0442bc854ec8be9d5c3839f892ea97fcd2a4b5d62225bbf47e863a472bbc1eb1
    naming_event = Event(
        block_number=836053,
        transaction_index=1,
        event_index=1,
        contract_address=to_bytes("0x06ac597f8116f886fa1c97a23fa4e08299975ecaf6b598873ca6792b9bbfb678"),
        keys=[
            starknet_keccak(b"AddressToDomainUpdate"),
            to_bytes("0x62cf279668311fb3850dafdfe3f8ed00ec72f1e824056633c9bfc7940de19ce"),
        ],
        data=[
            to_bytes("0x2"),
            to_bytes("0x944f11e22979"),
            to_bytes("0xce31cfe97"),
        ],
        event_name=None,
        decoded_params={},
        class_hash=to_bytes("0x027bb37f5b8cbf4fd29f1042f5574e6b6faeda9951bad9571b54af56887966b7"),
    )

    starknet_id_updates = parse_starknet_id_updates([naming_event])

    assert starknet_id_updates[0].identity == starknet_keccak(b"villanita.braavos.stark")
    assert starknet_id_updates[0].kind == StarknetIDUpdateKind.subdomain_to_address_update
    assert starknet_id_updates[0].data == {
        "domain": "villanita.braavos.stark",
        "address": to_bytes("0x62cf279668311fb3850dafdfe3f8ed00ec72f1e824056633c9bfc7940de19ce"),
    }

    starknet_ids, domains, id_map = generate_starknet_id_state(
        identity_state={}, address_to_domain={}, address_to_identity={}, starknet_id_updates=starknet_id_updates
    )

    assert len(starknet_ids) == 0
    assert len(id_map) == 0
    assert len(domains) == 1

    assert (
        domains[to_bytes("0x62cf279668311fb3850dafdfe3f8ed00ec72f1e824056633c9bfc7940de19ce")]
        == "villanita.braavos.stark"
    )


# https://voyager.online/tx/0x7dc6fc8d6c8feda05d719dcd8664ed7cc7c6aa3ac67af65946f24bc8ea75abe#events
# Register Subdomain, Identity NFT Transfer, & Verifier Data Update
@pytest.mark.asyncio
async def test_parse_starknet_id_state(starknet_rpc_url, async_http_session):
    _, _, events, _ = await get_blocks_with_txns([861040], starknet_rpc_url, async_http_session)
    filtered_events = [e for e in events if e.transaction_index == 0]

    starknet_id_updates = parse_starknet_id_updates(filtered_events)
    # assert len(starknet_id_updates) == 2

    assert starknet_id_updates[0].identity == (73857595493).to_bytes(32, "big")
    assert starknet_id_updates[0].kind == StarknetIDUpdateKind.identity_update
    assert starknet_id_updates[0].data == {
        "domains": [
            (
                "aliaksandra.stark",
                1761933498,
            )
        ],
        "new_owner": to_bytes("0x077b8e5a28ebee88712bf92405d3c9fdcaad66310232305bf3df91a365140bc5"),
        "old_owner": None,
    }

    assert starknet_id_updates[1].identity == (73857595493).to_bytes(32, "big")
    assert starknet_id_updates[1].kind == StarknetIDUpdateKind.identity_data_update
    assert starknet_id_updates[1].data == {
        "verifier_data": {
            "name": (
                [to_bytes("07053be99dead06f61801c9b5ca6543793cd63d282edf0bfac5e3acaecf103f5")],
                to_bytes("06ac597f8116f886fa1c97a23fa4e08299975ecaf6b598873ca6792b9bbfb678"),
            ),
            "nft_pp_contract": (
                [to_bytes("076503062d78f4481be03c9145022d6a4a71ec0719aa07756f79a2384dc7ef16")],
                to_bytes("070aaa20ec4a46da57c932d9fd89ca5e6bb9ca3188d3df361a32306aff7d59c7"),
            ),
            "nft_pp_id": (
                [to_bytes("0x1b4be9a55e"), to_bytes("0x00")],
                to_bytes("070aaa20ec4a46da57c932d9fd89ca5e6bb9ca3188d3df361a32306aff7d59c7"),
            ),
        },
        "user_data": None,
    }

    starknet_ids, domains, id_map = generate_starknet_id_state({}, {}, {}, starknet_id_updates)

    assert len(starknet_ids) == 1
    assert len(domains) == 0
    assert len(id_map) == 1

    assert id_map[to_bytes("0x077b8e5a28ebee88712bf92405d3c9fdcaad66310232305bf3df91a365140bc5")] == 0x1132417865

    id_data = starknet_ids[0x1132417865]
    assert id_data.domain == "aliaksandra.stark"


def test_parse_v0_braavos_subdomain():
    pass
