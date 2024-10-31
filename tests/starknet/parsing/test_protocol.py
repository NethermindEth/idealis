from nethermind.starknet_abi.utils import starknet_keccak

from nethermind.idealis.parse.starknet.protocol.starknet_id import parse_starknet_id_updates, generate_starknet_ids
from nethermind.idealis.types.starknet import Event
from nethermind.idealis.utils import to_bytes
from nethermind.idealis.utils.starknet import (
    decode_starknet_id_domain,
    encode_starknet_id_domain,
)


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
        class_hash=to_bytes("0x027bb37f5b8cbf4fd29f1042f5574e6b6faeda9951bad9571b54af56887966b7")
    )

    starknet_id_updates = parse_starknet_id_updates([naming_event])

    assert starknet_id_updates[0].owner_update is None
    assert starknet_id_updates[0].domain_name == "villanita.braavos.stark"
    assert starknet_id_updates[0].updated_resolve_contract

    starknet_ids = generate_starknet_ids({}, starknet_id_updates)

    assert len(starknet_ids) == 1

    assert starknet_ids['villanita.braavos.stark'].resolve_address == to_bytes(
        "0x62cf279668311fb3850dafdfe3f8ed00ec72f1e824056633c9bfc7940de19ce"
    )
    assert starknet_ids['villanita.braavos.stark'].expire_timestamp is None


def test_parse_starknet_id_state():
    pass


def test_parse_v0_braavos_subdomain():
    pass
